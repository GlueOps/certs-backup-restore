FROM python:3.15.2-alpine@sha256:a0f2e268f2ce8f3709611a90054ec6a8ae31f6251f5896b8648b9bb99835e30a

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
