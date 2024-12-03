FROM python:3.11.10-alpine@sha256:65c34f59d896f939f204e64c2f098db4a4c235be425bd8f0804fd389b1e5fd80

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
