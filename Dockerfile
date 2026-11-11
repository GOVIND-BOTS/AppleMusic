FROM python:3.10-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -U pip wheel \
    && pip3 uninstall -y motor pymongo || true \
    && pip3 install --no-cache-dir -U -r requirements.txt

COPY . .

CMD ["bash", "start"]
