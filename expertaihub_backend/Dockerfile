# expertaihub_backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ----- system packages ----------------------------------------------------
RUN apt-get update -qq && \
    # Git (needed by your ingestion script)
    apt-get install -y --no-install-recommends git && \
    # OpenGL / X-stub libs required by pymupdf, opencv, etc.
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 && \
    # PDF utilities / OCR (optional but handy)
    apt-get install -y --no-install-recommends \
        poppler-utils \
        tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# --------------------------------------------------------------------------

COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
EXPOSE 8000
CMD ["uvicorn","expertaihub_backend.asgi:application","--host","0.0.0.0","--port","8000"]
