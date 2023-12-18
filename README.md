## Kubernetes TLS Secrets Backup and Restore

This Python program simplifies Kubernetes TLS certificate management using Amazon S3 for backup and restore.

### Usage 

```bash
python main.py --backup
python main.py --restore
```

### Environment Variables

```bash
BUCKET_NAME    ="your-s3-bucket-name"
AWS_ACCESS_KEY ="your-aws-access-key"
AWS_SECRET_KEY ="your-aws-secret-key"
BUCKET_REGION  ="your-s3-bucket-region"
```