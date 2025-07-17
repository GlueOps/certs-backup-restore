FROM python:3.12.11-alpine@sha256:9b8808206f4a956130546a32cbdd8633bc973b19db2923b7298e6f90cc26db08

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
