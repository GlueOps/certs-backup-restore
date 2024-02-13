import os 
import yaml
import boto3
import logging
import argparse
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

def get_latest_backup():
    s3 = boto3.client('s3')

    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name,Prefix=captain_domain+"/"+backup_prefix)
    latest_snap_object = None
    for page in page_iterator:
        if "Contents" in page:
            snap_objects = [obj for obj in page['Contents'] if obj['Key'].endswith(output_file)]
            if snap_objects:
                current_latest_snap_object = max(snap_objects, key=lambda obj: obj['LastModified']) 
            if (latest_snap_object is None or 
                current_latest_snap_object['LastModified'] > latest_snap_object['LastModified']):
                latest_snap_object = current_latest_snap_object

    if latest_snap_object:
        # Download the latest secrets.yaml file
        local_file_path = os.path.join(output_file)
        s3.download_file(bucket_name, latest_snap_object['Key'], local_file_path)
        logger.info(f"Downloaded the latest backup from s3: {latest_snap_object['Key']}")
        return local_file_path
    else:
        logger.info("No secrets.yaml files found in the specified S3 location.")
        return None
    
def restore_tls_secrets():

    exclude_namespaces = os.getenv("EXCLUDE_NAMESPACES").split(',')
    with open(output_file, 'r') as file:
        secrets_yaml = file.read()
        secrets_data = yaml.load_all(secrets_yaml, Loader=yaml.SafeLoader)
        api = k8s_client.CoreV1Api()

        try:
            for secret_dict in secrets_data:
                namespace = secret_dict['metadata']['namespace']
                if(namespace not in exclude_namespaces):
                    # Create a V1Secret object from the dictionary
                    secret = k8s_client.V1Secret(
                        metadata=k8s_client.V1ObjectMeta(
                        name=secret_dict['metadata']['name'],
                        namespace=secret_dict['metadata']['namespace'],
                        annotations=secret_dict['metadata']['annotations'],
                        labels=secret_dict['metadata']['labels']
                        ),
                        data=secret_dict.get('data', {}),
                        type=secret_dict.get('type', None)
                    )

                    api.create_namespaced_secret(
                        namespace=secret.metadata.namespace,
                        body=secret,
                    )
                    logger.info(f"Secret '{secret.metadata.name}' applied in namespace {secret.metadata.namespace}")
        except k8s_client.rest.ApiException as e:
            logger.error(f"Error applying secrets: {e}")