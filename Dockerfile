FROM python:3.11.11-alpine@sha256:bc84eb94541f34a0e98535b130ea556ae85f6a431fdb3095762772eeb260ffc3

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
