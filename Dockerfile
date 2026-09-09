# Portable image: works on Render, Railway, Fly.io, Cloud Run, or any VPS.
FROM python:3.13-slim

# Tesseract makes image OCR actually work in production. It is the one piece
# the app cannot ship in requirements.txt, and without it photo uploads fall
# back to "OCR engine not available".
# hindi + english language packs, since the app is bilingual.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PHYSIO_ENV=production \
    PHYSIO_DATABASE_URL=sqlite:////data/physio.db \
    PHYSIO_UPLOAD_DIR=/data/uploads

WORKDIR /app

# Dependencies first so code edits do not bust the layer cache.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Medical uploads and the database live on the mounted volume, never in the
# image layer -- anything written outside /data is lost on redeploy.
RUN mkdir -p /data/uploads \
    && useradd --create-home --uid 10001 physio \
    && chown -R physio:physio /data /app
USER physio

EXPOSE 8000

# Most hosts inject $PORT; default to 8000 for plain `docker run`.
#
# --proxy-headers makes uvicorn read the client address from X-Forwarded-For,
# which rate limiting keys on -- without it every request appears to come from
# the reverse proxy and one attacker would exhaust everyone's budget. It is
# only honoured for hosts in --forwarded-allow-ips, so the default stays at
# loopback and compose widens it to the internal network where only Caddy sits.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-127.0.0.1}"]
