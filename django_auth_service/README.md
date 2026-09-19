# Django auth service

Owns identity only: registration, login, JWT access/refresh tokens (RS256,
rotated + blacklisted), sessions for the admin site, CORS, rate limiting on
auth endpoints, and request logging to a rotating file. FastAPI verifies
tokens issued here using the public key alone — no shared secret, no
network call between services.

## Setup

```bash
cd django_auth_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit values, especially DJANGO_SECRET_KEY

# A dev RS256 keypair ships in core/keys/ so this runs out of the box —
# regenerate it before any real deployment, since a shared example
# private key is not a secret:
openssl genrsa -out core/keys/private.pem 2048
openssl rsa -in core/keys/private.pem -pubout -out core/keys/public.pem

# Postgres + Redis must be running and reachable per your .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Endpoints

| Method | Path             | Auth        | Purpose                                   |
|--------|------------------|-------------|--------------------------------------------|
| POST   | `/auth/register/`| none        | Create a user                              |
| POST   | `/auth/login/`   | none (5/min)| Get `access` + `refresh` tokens            |
| POST   | `/auth/refresh/` | none (20/min)| Exchange refresh for new access+refresh   |
| POST   | `/auth/logout/`  | Bearer      | Blacklist the given refresh token          |
| GET    | `/auth/me/`      | Bearer      | Current user's profile                     |

## Example flow

```bash
curl -X POST localhost:8000/auth/login/ -d '{"username":"alice","password":"..."}' -H "Content-Type: application/json"
# -> {"access": "...", "refresh": "..."}

curl localhost:8000/auth/me/ -H "Authorization: Bearer <access>"

curl -X POST localhost:8000/auth/refresh/ -d '{"refresh":"<refresh>"}' -H "Content-Type: application/json"
# -> new access + refresh; old refresh is now blacklisted

curl -X POST localhost:8000/auth/logout/ -d '{"refresh":"<refresh>"}' -H "Authorization: Bearer <access>" -H "Content-Type: application/json"
```

## How FastAPI verifies these tokens

Copy `core/keys/public.pem` to the FastAPI service and verify with PyJWT:

```python
import jwt

payload = jwt.decode(token, public_key_pem, algorithms=["RS256"])
user_id, role = payload["user_id"], payload["role"]
```

No database lookup needed for verification — only `/auth/refresh/` and
`/auth/logout/` touch the database (to check/set the blacklist).

## What's deliberately industrial here, and why

- **RS256, not HS256** — asymmetric signing means the API service that
  verifies tokens never holds the key that can mint them.
- **Refresh rotation + blacklist** — every refresh call invalidates the
  token that was just used, so a stolen refresh token is only useful once.
- **Scoped throttling on `/login/` and `/refresh/`** — separate from any
  general-purpose API rate limiting, since these are the endpoints
  attackers actually hit.
- **Custom User model from day one** — swapping this in later, after
  migrations exist, is one of the most painful things to retrofit in Django.
- **Rotating file logs with a request id** — every response carries
  `X-Request-ID`, so a single log line ties a user's request to what
  happened, and you can correlate it with the FastAPI service's logs too.
