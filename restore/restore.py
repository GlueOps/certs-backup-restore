import os 
import yaml
import boto3
import logging
from datetime import datetime, timedelta, timezone

from kubernetes import (
  client as k8s_client,
  config as k8s_config
)
 
output_file = "secrets.yaml"
bucket_name = os.getenv("BUCKET_NAME")
captain_domain = os.getenv("CAPTAIN_DOMAIN")
backup_prefix = os.getenv("BACKUP_PREFIX")

#init child logger
logger = logging.getLogger('CERT_BACKUP_RESTORE.config')

BACKUP_FILENAME = "secrets.yaml"
WALK_DAYS = 185  # four of the five in-scope secrets outlive any shorter bound


def get_latest_backup():
    """Newest backup key, downloaded to output_file. Returns the local path, or None.

    Ported from GlueOps/vault-init-controller. Only the key SELECTION is ported: this
    codebase's contract is to download and return a local path, and returning the S3
    object dict instead would leave restore_tls_secrets() opening a file nobody wrote.

    Walks date prefixes backwards rather than listing the whole prefix and calling
    get_object_tagging() on every object.
    """
    s3 = boto3.client("s3")
    prefix = f"{captain_domain}/{backup_prefix}/".replace("//", "/")

    probe = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
    if not probe.get("Contents"):
        logger.info(f"No backups found under s3://{bucket_name}/{prefix}")
        return None

    paginator = s3.get_paginator("list_objects_v2")
    today = datetime.now(timezone.utc).date()
    for days_ago in range(WALK_DAYS):
        day = today - timedelta(days=days_ago)
        newest = None
        for page in paginator.paginate(Bucket=bucket_name, Prefix=f"{prefix}{day.isoformat()}/"):
            for obj in page.get("Contents", []):
                if os.path.basename(obj["Key"]) == BACKUP_FILENAME:
                    newest = obj["Key"]
        if newest:
            s3.download_file(bucket_name, newest, output_file)
            logger.info(f"Restoring from s3://{bucket_name}/{newest}")
            return output_file

    # Keys exist but none matched: an anomaly, not an empty bucket. Distinct message.
    logger.error(f"Backups exist under {prefix} but none within the last {WALK_DAYS} "
                 f"days matched {BACKUP_FILENAME}; restoring nothing")
    return None


ALLOWED_TYPES = {"kubernetes.io/tls", "Opaque"}
# Copying these verbatim from a backup would let a tampered object mint a
# ServiceAccount token; nothing cert-manager produces needs them.
STRIPPED_ANNOTATIONS = ("kubernetes.io/service-account.name",
                        "kubernetes.io/service-account.uid")


def _ensure_namespace(api, namespace):
    """Create the namespace if absent. At PreSync most application namespaces do not
    exist yet - glueops-core-vault is created at sync-wave 4, long after this runs."""
    try:
        api.create_namespace(k8s_client.V1Namespace(
            metadata=k8s_client.V1ObjectMeta(name=namespace)))
        logger.info(f"Created namespace {namespace}")
    except k8s_client.rest.ApiException as e:
        if e.status != 409:  # 409 = already exists, including while Terminating
            raise


def restore_tls_secrets():
    """Create every backed-up Secret that is not already present.

    create-only: the API refuses to overwrite an existing Secret, so live material can
    never be replaced by a stale snapshot. Runs on every sync of the cert-manager
    Application, which is safe precisely because of that.
    """
    exclude_namespaces = (os.getenv("EXCLUDE_NAMESPACES") or "").split(",")
    api = k8s_client.CoreV1Api()
    counts = dict(selected=0, created=0, skipped_exists=0, skipped_excluded=0,
                  rejected_type=0, skipped_ns_terminating=0, failed=0)

    with open(output_file) as file:
        documents = list(yaml.safe_load_all(file.read()))

    for secret_dict in documents:
        if not secret_dict:
            continue
        counts["selected"] += 1
        meta = secret_dict.get("metadata", {})
        namespace, name = meta.get("namespace"), meta.get("name")
        try:
            if namespace in exclude_namespaces:
                counts["skipped_excluded"] += 1
                continue

            # A backed-up Secret is cert material or nothing.
            secret_type = secret_dict.get("type") or "Opaque"
            if secret_type not in ALLOWED_TYPES:
                logger.warning(f"Rejecting {namespace}/{name}: type {secret_type}")
                counts["rejected_type"] += 1
                continue

            # Verbatim metadata, minus the service-account keys. cert-manager compares
            # the issuer annotations to decide whether to adopt a Secret or re-issue:
            # dropping even one of them triggers a fresh certificate. issuer-kind and
            # issuer-group are empty strings rather than absent, so nothing may be
            # discarded for being falsy.
            annotations = dict(meta.get("annotations") or {})
            for key in STRIPPED_ANNOTATIONS:
                annotations.pop(key, None)

            _ensure_namespace(api, namespace)
            api.create_namespaced_secret(namespace=namespace, body=k8s_client.V1Secret(
                metadata=k8s_client.V1ObjectMeta(
                    name=name,
                    namespace=namespace,
                    annotations=annotations,
                    labels=meta.get("labels") or {},
                ),
                data=secret_dict.get("data", {}),
                type=secret_type,
            ))
            logger.info(f"Created {namespace}/{name}")
            counts["created"] += 1

        except k8s_client.rest.ApiException as e:
            if e.status == 409:
                logger.info(f"Keeping live {namespace}/{name}")
                counts["skipped_exists"] += 1
            elif e.status == 403 and "being terminated" in str(e.body):
                # Emitted by NamespaceLifecycle admission on the Secret create, not on
                # the namespace create. Transient; the next sync retries.
                logger.warning(f"Namespace {namespace} terminating, will retry next sync")
                counts["skipped_ns_terminating"] += 1
            else:
                logger.error(f"Failed {namespace}/{name}: {e}")
                counts["failed"] += 1
        except Exception as e:
            # Per-secret, and Exception not ApiException: a KeyError here previously
            # escaped the handler entirely and abandoned every remaining secret.
            logger.error(f"Failed {namespace}/{name}: {e}")
            counts["failed"] += 1

    logger.info("restore_summary " + " ".join(f"{k}={v}" for k, v in counts.items()))
    accounted = sum(v for k, v in counts.items() if k != "selected")
    if accounted != counts["selected"]:
        logger.warning(f"Counter mismatch: {accounted} accounted vs "
                       f"{counts['selected']} parsed")
