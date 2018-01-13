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
