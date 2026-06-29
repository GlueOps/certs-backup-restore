## Kubernetes TLS Secrets Backup and Restore

This Python program simplifies Kubernetes TLS certificate management using Amazon S3 for backup and restore.

### Usage 

```bash
python main.py --backup
python main.py --restore
```

### Environment Variables

**AWS credentials** are read from the standard boto3 credential chain. When using static
keys, the variable names must be the ones boto3 recognizes (when running in-cluster with an
IRSA / IAM role, these are not needed):

```bash
AWS_ACCESS_KEY_ID     ="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY ="your-aws-secret-access-key"
AWS_REGION            ="your-s3-bucket-region"   # or AWS_DEFAULT_REGION
```

**Application configuration:**

```bash
BUCKET_NAME        ="your-s3-bucket-name"   # required (backup + restore)
CAPTAIN_DOMAIN     ="your-cluster-domain"   # required; first path segment of the S3 key
BACKUP_PREFIX      ="tls-secrets"           # required; second path segment of the S3 key
EXCLUDE_NAMESPACES ="kube-system,default"   # required for --restore; comma-separated
RESTORE_THIS_BACKUP="secrets.yaml"          # optional (--restore); pin a specific backup file
PYTHON_LOG_LEVEL   ="INFO"                  # optional; defaults to INFO
```

Backups are written to `s3://$BUCKET_NAME/$CAPTAIN_DOMAIN/$BACKUP_PREFIX/<YYYY-MM-DD>/secrets.yaml`.