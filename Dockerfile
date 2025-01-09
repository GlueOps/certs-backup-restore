FROM python:3.11.11-alpine@sha256:9af3561825050da182afc74b106388af570b99c500a69c8216263aa245a2001b

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
