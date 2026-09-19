# Testcraft frontend

React + Vite. Talks to the Django auth service for login/register/refresh
and to the FastAPI service for upload/generate — no other backend calls.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # defaults already match the other services' default ports
npm run dev
```

Opens on `http://localhost:5173`. Both backends' `CORS_ALLOWED_ORIGINS`
already default to this origin — if you change the frontend's port, update
`CORS_ALLOWED_ORIGINS` in both `django_auth_service/.env` and
`fastapi_service/.env` to match.

## Pages

| Route        | Purpose                                              |
|--------------|-------------------------------------------------------|
| `/login`     | Sign in, gets access + refresh tokens                |
| `/register`  | Create an account                                     |
| `/`          | Upload a file → view structure report → generate tests |

## How auth actually works here

- The **access token lives in memory only** (a JS variable), never in
  `localStorage` — so it can't be read back by an XSS payload after the
  fact. It's gone on page reload by design.
- The **refresh token lives in `localStorage`** so a reload doesn't force
  a re-login. On load, `AuthContext` checks for a stored refresh token and
  calls `/auth/me/` to restore the session — this call transparently
  refreshes the access token if needed.
- Every API call goes through `api/http.js`, which retries exactly once
  on a `401` by calling `/auth/refresh/` and retrying the original
  request with the new access token. Refresh rotation on the backend
  means the old refresh token is dead the moment this happens.
- **Production note**: `localStorage` for the refresh token is a
  reasonable default for a scaffold, but a real deployment should have
  Django set the refresh token as an `httpOnly` cookie instead — that
  requires a small change to the login/refresh views on the backend
  (SIMPLE_JWT doesn't do this automatically) so JavaScript never has
  direct access to it at all.

## Design notes

The palette is deliberately not a generic SaaS look: colors are borrowed
from diff/CI semantics (forest green = pass, rust = warning, slate = code)
since this is a tool for reviewing generated tests and static-analysis
warnings, not a marketing page. IBM Plex Mono is used specifically for
code, filenames, and structural data (line numbers, function signatures)
because the subject matter is code — not as a decorative label font.
Panels are flat with a single hairline border rather than the
identical-rounded-card-with-soft-shadow pattern.

## Build for production

```bash
npm run build   # outputs static files to dist/
```

`dist/` is plain static HTML/CSS/JS — serve it with any static file host
or behind the same nginx reverse proxy fronting the two backend services.
