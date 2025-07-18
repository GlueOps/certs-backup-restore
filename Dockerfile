FROM python:3.11.13-alpine@sha256:9ce54d7ed458f71129c977478dd106cf6165a49b73fa38c217cc54de8f3e2bd0

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
