FROM python:3.12.11-alpine@sha256:c610e4a94a0e8b888b4b225bfc0e6b59dee607b1e61fb63ff3926083ff617216

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
