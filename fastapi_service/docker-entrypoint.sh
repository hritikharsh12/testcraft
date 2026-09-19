#!/bin/sh
set -e

# app.core.config reads keys/public.pem at import time, so nothing here can
# run until Django's entrypoint has generated it onto the shared volume.
echo "[entrypoint] waiting for public.pem from the auth service..."
until [ -f /app/keys/public.pem ]; do
  sleep 1
done

echo "[entrypoint] waiting for postgres at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  sleep 1
done

echo "[entrypoint] applying alembic migrations..."
alembic upgrade head

# Seeding is idempotent-by-marker: without this guard, every container
# restart would duplicate the whole knowledge base.
if [ ! -f /app/.rag_seeded ]; then
  echo "[entrypoint] seeding RAG knowledge base..."
  python -m app.services.rag.seed && touch /app/.rag_seeded
fi

echo "[entrypoint] starting fastapi on :8001"
exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload
