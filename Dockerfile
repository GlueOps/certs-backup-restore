FROM python:3.11.12-alpine@sha256:a648a482d0124da939ead54c5c6f0f6ce0b4ac925749c7d9ad3c2eba838966f1

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
