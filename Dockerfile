FROM python:3.14.9-alpine@sha256:d55673c233e28839c1c0c69766428cb6d50174a2ecfdcf915b6f58a0b0991562

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
