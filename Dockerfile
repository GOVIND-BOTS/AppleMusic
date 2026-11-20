FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Node.js 22 is required by the bundled bgutil PO-token provider.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git curl ca-certificates gnupg build-essential \
    libglib2.0-0 libgl1 libsm6 libxext6 libxrender1 libgomp1 \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && ffmpeg -version && ffprobe -version && node --version && npm --version \
    && rm -rf /var/lib/apt/lists/*

# Build the official PO-token provider into this same image.
RUN git clone --depth 1 --branch 2.0.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /tmp/bgutil-ytdlp-pot-provider \
    && cd /tmp/bgutil-ytdlp-pot-provider/server \
    && npm ci && npx tsc && npm prune --omit=dev \
    && mkdir -p /opt/bgutil-provider \
    && cp -a . /opt/bgutil-provider/ \
    && rm -rf /tmp/bgutil-ytdlp-pot-provider

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --upgrade pip wheel \
    && (pip3 uninstall -y motor pymongo || true) \
    && pip3 install -r requirements.txt

RUN python -c "import sys; print('Python:', sys.version)" \
    && python -c "import PIL; print('Pillow: OK')" \
    && ffmpeg -filters >/dev/null \
    && node --version \
    && test -f /opt/bgutil-provider/build/main.js

COPY . .
RUN mkdir -p /app/downloads/editor /app/cache

CMD ["bash", "start"]
