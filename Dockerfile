FROM python:3.13.7-alpine@sha256:587df003ff48316a56a0ddac50e1e2b64dfeca281f0c071b91920895a65b12d2

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
