FROM python:3.15.1-alpine@sha256:e85751f6fe48ddb0619557d606ad93685134347a821b85fd9cd9dfa61addb970

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
