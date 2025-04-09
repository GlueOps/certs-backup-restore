FROM python:3.12.10-alpine@sha256:c08bfdbffc9184cdfd225497bac12b2c0dac1d24bbe13287cfb7d99f1116cf43

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
