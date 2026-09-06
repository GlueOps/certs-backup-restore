import os
import sys
import argparse
from glueops.setup_logging import configure as go_configure_logging
from kubernetes import (
  config as k8s_config
)
from backup import backup
from restore import restore


output_file = "secrets.yaml"

# configure logger
logger = go_configure_logging(
    name='CERT_BACKUP_RESTORE',
    level=os.getenv('PYTHON_LOG_LEVEL', 'INFO')
)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CLI used to backup and restore k8s tls secrets")
    parser.add_argument("--backup", action="store_true", help="backs up tls secrets in s3")
    parser.add_argument("--restore", action="store_true", help="restore tls secrets from s3 in k8s")

    args = parser.parse_args()

    # setting cluster config
    try:
        k8s_config.load_incluster_config()
        logger.info("Loaded incluster kubeconfig")
    except Exception as e:
        logger.warning(f'Error loading in-cluster k8s config: {e}')
        try:
            logger.info('Using local Kubeconfig (not in-cluster)')
            k8s_config.load_kube_config()
        except Exception:
            logger.exception('Failed to load Kubeconfig from cluster, local file')

    if args.backup:
        if not backup.cert_manager_namespace:
            logger.error("CERT_MANAGER_NAMESPACE is not set; refusing to run. "
                         "It must equal the namespace cert-manager runs in, or ACME "
                         "account keys will be silently omitted from the backup.")
            sys.exit(1)
        try:
            all_tls_secrets = backup.get_tls_secrets()

            # An empty capture must never be uploaded. The day's S3 key is overwritten
            # in place, so uploading nothing would replace a good backup with a useless
            # one - and a wrong selector returns [] with no exception, so this is the
            # only thing standing between a selector bug and silent data loss.
            if not all_tls_secrets:
                logger.error("Captured 0 secrets; refusing to upload an empty backup "
                             "over the existing one.")
                sys.exit(1)

            backup.write_secrets_to_file(all_tls_secrets, output_file)
            logger.info(f"Backed up {len(all_tls_secrets)} secret(s) to {output_file}")
            backup.upload_secrets_to_s3()

        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Error backing up secrets: {e}")
            sys.exit(1)
            
    if args.restore:
        try:
            latest_backup = restore.get_latest_backup()
            if latest_backup:
                restore.restore_tls_secrets()
            else:
                logger.info("No backups found.")
        except Exception as e:
            logger.error(f"Error restoring secrets: {e}")
    
    else:
        exit()
    if os.path.exists(output_file):
        os.remove(output_file)