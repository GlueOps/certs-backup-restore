import logging
import yaml
import boto3
import os
import datetime
from kubernetes import (
  client as k8s_client,
  config as k8s_config
)

output_file = "secrets.yaml"
bucket_name = os.getenv("BUCKET_NAME")
captain_domain = os.getenv("CAPTAIN_DOMAIN")
backup_prefix = os.getenv("BACKUP_PREFIX")
# The namespace cert-manager runs in, which is where ClusterIssuer ACME account-key
# Secrets live. Supplied by the chart because this job runs in its own namespace and
# cannot derive it. Hard-fail rather than guess: a wrong value silently produces a
# backup with no account keys.
cert_manager_namespace = os.getenv("CERT_MANAGER_NAMESPACE")

#init child logger
logger = logging.getLogger('CERT_BACKUP_RESTORE.config')


def handle_error_and_exit(msg):
    logger.error(msg)
    exit(1)

# Certificate output Secrets carry controller.cert-manager.io/fao=true on every
# cert-manager release from v1.11.0 to current, applied unconditionally and
# back-filled on upgrade. cert-manager's transient next-private-key Secrets carry
# it too, so they are excluded server-side; that label predates fao (v1 API, 2020).
CERT_SECRET_SELECTOR = "controller.cert-manager.io/fao=true,!cert-manager.io/next-private-key"


def get_tls_secrets():
    """Every Secret cert-manager manages: Certificate outputs plus ACME account keys.

    A listing failure is fatal - returning [] here would be indistinguishable from
    "this cluster has no certificates" and would upload an empty backup over a good one.
    """
    v1 = k8s_client.CoreV1Api()
    found = {}

    for secret in v1.list_secret_for_all_namespaces(label_selector=CERT_SECRET_SELECTOR).items:
        found[(secret.metadata.namespace, secret.metadata.name)] = secret
    logger.info(f"Found {len(found)} Certificate output secret(s)")

    for namespace, name in _acme_account_key_refs():
        if (namespace, name) in found:
            continue
        try:
            found[(namespace, name)] = v1.read_namespaced_secret(name, namespace)
            logger.info(f"Found ACME account key {namespace}/{name}")
        except k8s_client.rest.ApiException as e:
            # Not fatal: the Secret legitimately does not exist for a window on a
            # fresh bootstrap, and with disableAccountKeyGeneration it may never exist.
            logger.warning(f"ACME account key {namespace}/{name} not readable ({e.status}); skipping")

    return list(found.values())


def _acme_account_key_refs():
    """(namespace, name) of every ACME account key, found via the issuers that own them.

    These Secrets do NOT carry the fao label, so the selector above misses them. They
    are located through .spec.acme.privateKeySecretRef instead, which exists on every
    cert-manager version - unlike app.kubernetes.io/managed-by=cert-manager, which is
    write-once, only exists from v1.18.0, and marks the webhook CA on v1.16-v1.17.
    """
    custom = k8s_client.CustomObjectsApi()
    refs = []

    def ref_of(issuer):
        return (issuer.get("spec") or {}).get("acme", {}).get("privateKeySecretRef", {}).get("name")

    # ClusterIssuers are cluster-scoped: metadata.namespace is "", so their Secrets
    # live in cert-manager's --cluster-resource-namespace, which this job cannot
    # derive (it runs in its own namespace, not cert-manager's).
    for issuer in custom.list_cluster_custom_object(
            "cert-manager.io", "v1", "clusterissuers").get("items", []):
        name = ref_of(issuer)
        if name:
            refs.append((cert_manager_namespace, name))

    for issuer in custom.list_cluster_custom_object(
            "cert-manager.io", "v1", "issuers").get("items", []):
        name = ref_of(issuer)
        if name:
            refs.append((issuer["metadata"]["namespace"], name))

    return refs
    
def write_secrets_to_file(secrets, output_file):
    with open(output_file, 'w') as file:
        for index, secret in enumerate(secrets):
            secret_dict = k8s_client.ApiClient().sanitize_for_serialization(secret)
            secret_dict['apiVersion'] = 'v1'
            secret_dict['kind'] = 'Secret'
            if 'kubectl.kubernetes.io/last-applied-configuration' in secret_dict:
                del secret_dict['kubectl.kubernetes.io/last-applied-configuration']
            secret_yaml = yaml.dump(secret_dict)
            file.write(secret_yaml)
            if index < len(secrets) - 1:
                file.write('\n---\n')

def upload_secrets_to_s3():
    try:
        s3 = boto3.client('s3')
        current_datetime = datetime.datetime.now(datetime.UTC)
        current_date = current_datetime.strftime("%Y-%m-%d")
        current_date_with_time = current_datetime.strftime('%Y-%m-%dT%H:%M:%S')

        s3_key = captain_domain+"/"+backup_prefix+"/"+current_date+"/secrets.yaml"
        s3.upload_file(
	            output_file,
	            bucket_name,
	            s3_key,
	            ExtraArgs={
	                'Tagging': f"datetime_created={current_date_with_time}"
	            }
        )
        logger.info(f"File uploaded to S3: {bucket_name}/{s3_key}")
    except FileNotFoundError:
        handle_error_and_exit(f"The file {output_file} was not found.")
    except Exception as e:
        handle_error_and_exit(f"An error occurred: {str(e)}")
