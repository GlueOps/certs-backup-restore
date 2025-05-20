FROM python:3.11.12-alpine@sha256:d0199977fdae5d1109a89d0b0014468465e014a9834d0a566ea50871b3255ade

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
