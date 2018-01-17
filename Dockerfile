FROM python:3

RUN apt-get update && apt-get install -y --no-install-recommends \
		ca-certificates \
		libssl-dev \
        openssl \
        libacl1-dev \
        libacl1 \
        build-essential \
        libfuse-dev \
        fuse \
        pkg-config \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir borgbackup

VOLUME ["/backup"]

ENV SAFEPLAN_ID NOT_SET

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY swagger_server /usr/src/app
COPY backup-agent-web/dist /usr/src/app/web

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["app.py"]