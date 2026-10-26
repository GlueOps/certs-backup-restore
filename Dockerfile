FROM python:3.15.2-alpine@sha256:827d76cd0da4f700a703df95e7a70fec2ecc7fa9fd528638ab2e8aa96fbf8e0e

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
