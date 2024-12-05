FROM python:3.11.11-alpine@sha256:fbcb089a803d5673f225dc923b8e29ecc7945e9335465037b6961107b9da3d61

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
