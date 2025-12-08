FROM python:3.14.2-alpine@sha256:f74e244c26cf94c81a2a6ec8e4e5e55e59bae979063c83382cafb87f03fc1f56

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
