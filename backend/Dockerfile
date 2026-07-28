FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# /app is root-owned (created by WORKDIR/COPY above, before the USER switch below), so appuser
# can't mkdir a new child of it at runtime — retrieval_service.py's embedding cache needs
# /app/cache to already exist and be writable. Pre-creating + chowning it here means the cache
# works even with no volume mounted there (ephemeral, lost on container recreation); a real
# mount (see compose.yaml / infra/gce/docker-compose.yml) makes it persist across restarts too.
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/cache && \
    chown appuser:appuser /app/cache
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
