#!/bin/sh
set -e

KEY_DIR=/app/core/keys

# Django's RotatingFileHandler fails at startup if this doesn't exist, and
# empty directories often don't survive being zipped/downloaded.
mkdir -p /app/logs

# Generate the RS256 keypair on first run only. The keys live on a volume
# shared read-only with the FastAPI service, so the two stay in sync
# automatically instead of you copying public.pem around by hand.
if [ ! -f "$KEY_DIR/private.pem" ]; then
  echo "[entrypoint] generating RS256 keypair..."
  mkdir -p "$KEY_DIR"
  openssl genrsa -out "$KEY_DIR/private.pem" 2048 2>/dev/null
  openssl rsa -in "$KEY_DIR/private.pem" -pubout -out "$KEY_DIR/public.pem" 2>/dev/null
  chmod 644 "$KEY_DIR/public.pem"
fi

echo "[entrypoint] waiting for postgres at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  sleep 1
done

echo "[entrypoint] applying migrations..."
python manage.py migrate --noinput

# Creates an admin user only if one doesn't exist, so you can log in
# immediately without a manual createsuperuser step.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "[entrypoint] ensuring superuser exists..."
  python manage.py createsuperuser --noinput 2>/dev/null || true
fi

echo "[entrypoint] starting django on :8000"
exec python manage.py runserver 0.0.0.0:8000
