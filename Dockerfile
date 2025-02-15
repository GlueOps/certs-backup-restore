FROM python:3.11.11-alpine@sha256:d5e2fc72296647869f5eeb09e7741088a1841195059de842b05b94cb9d3771bb

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
