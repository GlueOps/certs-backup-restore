FROM python:3.11.9-alpine@sha256:0b5ed25d3cc27cd35c7b0352bac8ef2ebc8dd3da72a0c03caaf4eb15d9ec827a

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
