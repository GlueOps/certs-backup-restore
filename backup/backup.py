import logging
import yaml
import boto3
import os
from datetime import datetime
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

def get_tls_secrets():
    try:
        # Create a Kubernetes API client
        v1 = k8s_client.CoreV1Api()

        # Get secrets with type kubernetes.io/tls 
        all_namespaces = v1.list_namespace().items
        all_tls_secrets = []

        for namespace in all_namespaces:
            secrets = v1.list_namespaced_secret(namespace.metadata.name, label_selector='controller.cert-manager.io/fao=true').items
            all_tls_secrets.extend(secrets)
        return all_tls_secrets
    except Exception as e:
        logger.error(f"Error: {e}")
        return []
    
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
        current_date = datetime.now().strftime("%Y-%m-%d")
        s3_key = captain_domain+"/"+backup_prefix+"/"+current_date+"/secrets.yaml"
        s3.upload_file(output_file, bucket_name, s3_key)
        logger.info(f"File uploaded to S3: {bucket_name}/{s3_key}")
    except FileNotFoundError:
        logger.error(f"The file {output_file} was not found.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")