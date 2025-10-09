FROM python:3.14.0-alpine@sha256:e1a567200b6d518567cc48994d3ab4f51ca54ff7f6ab0f3dc74ac5c762db0800

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
