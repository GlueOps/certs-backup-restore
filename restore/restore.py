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
access_key = os.getenv("AWS_ACCESS_KEY")
secret_key = os.getenv("AWS_SECRET_KEY")
region = os.getenv("BUCKET_REGION","us-west-2")

#init child logger
logger = logging.getLogger('CERT_BACKUP_RESTORE.config')

def get_latest_backup():
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)

    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name)
    latest_date = None 
    
    for page in page_iterator:
        if "Contents" in page:
            dates = [datetime.strptime(obj['Key'][:10], '%Y-%m-%d') for obj in page['Contents']]
        latest_date = max(dates)

    if latest_date:
        # Formulate the latest date as part of the S3 object key
        latest_date_str = latest_date.strftime('%Y-%m-%d')
        latest_object_key = f"{latest_date_str}/secrets.yaml"

        # Download the latest secrets.yaml file
        local_file_path = os.path.join(output_file)
        s3.download_file(bucket_name, latest_object_key, local_file_path)
        logger.info(f"Downloaded the latest backup from s3: {latest_object_key}")
        return local_file_path
    else:
        logger.info("No secrets.yaml files found in the specified S3 location.")
        return None
    
def restore_tls_secrets():

    with open(output_file, 'r') as file:
        secrets_yaml = file.read()
        secrets_data = yaml.load_all(secrets_yaml, Loader=yaml.SafeLoader)
        api = k8s_client.CoreV1Api()

        try:
            for secret_dict in secrets_data:
                
                # Create a V1Secret object from the dictionary
                secret = k8s_client.V1Secret(
                    metadata=k8s_client.V1ObjectMeta(name=secret_dict['metadata']['name'],
                                                 namespace=secret_dict['metadata']['namespace']),
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