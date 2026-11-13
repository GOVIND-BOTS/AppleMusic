
FROM python:3.10-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# System dependencies + FFmpeg + Node.js 20
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    ca-certificates \
    gnupg \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
       | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
       > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && ffmpeg -version \
    && ffprobe -version \
    && node --version \
    && npm --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip3 install --upgrade pip wheel \
    && (pip3 uninstall -y motor pymongo || true) \
    && pip3 install -r requirements.txt

# Verify Python and FFmpeg
RUN python -c "import sys; print('Python:', sys.version)" \
    && python -c "import PIL; print('Pillow: OK')" \
    && ffmpeg -filters >/dev/null

# Copy bot source
COPY . .


RUN mkdir -p /app/downloads/editor \
    && mkdir -p /app/cache

# Start bot
CMD ["bash", "start"]
