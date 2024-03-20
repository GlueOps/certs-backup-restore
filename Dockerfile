FROM python:3.11.8-alpine3.19@sha256:65cb2034c64b4519f1481c552a30ae3fe19f47f3610513b0387dc2e1570080fa

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
