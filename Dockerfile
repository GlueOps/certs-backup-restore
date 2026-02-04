FROM python:3.14.3-alpine@sha256:e43b76c7e4a8a4621f4e84fd76e0dfb473eda5cc05fc58b2d4d640338eda48b1

WORKDIR /app

COPY . /app/cert-backup-restore

RUN pip3 install -r cert-backup-restore/requirements.txt

CMD ["python", "-u", "/app/cert-backup-restore/main.py","--backup"]
