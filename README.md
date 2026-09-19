# Testcraft — AI test case generator

Upload a source file, get generated tests and improvement suggestions back.
Built as a multi-service system to cover the patterns a real production
codebase uses.

## Architecture

| Service | Port | Responsibility |
|---------|------|----------------|
| `auth` (Django + DRF) | 8000 | Users, JWT access/refresh with rotation, sessions, admin |
| `api` (FastAPI) | 8001 | Upload, AST parsing, RAG retrieval, prompt building, LLM calls |
| `frontend` (React + Vite) | 5173 | Upload UI, structure report, generated test viewer |
| `postgres` | 5432 | Submissions, results, RAG knowledge base |
| `redis` | 6379 | Rate limiting, session cache |

The FastAPI service verifies Django-issued JWTs using only the **public**
key (RS256), so it can authenticate users but can never mint tokens. The
same pipeline is also exposed as an **MCP server** so MCP clients can call
`analyze_code` / `generate_tests` / `suggest_improvements` directly.

## Quick start (Docker — recommended)

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY to a real key
docker compose up --build
```

Then open **http://localhost:5173**.

That's it. Compose handles everything that used to be manual:
- generates the RS256 keypair on first run and shares it between services
  (read-only for FastAPI, so it can verify but never sign)
- waits for Postgres and Redis to be genuinely ready via healthchecks
- runs Django migrations and Alembic migrations
- seeds the RAG knowledge base once
- creates an admin user from `.env` so you can log in immediately

To reset everything including the database: `docker compose down -v`

## Manual setup (without Docker)

See the README in each service directory. Order matters — start
`django_auth_service` first, since it generates the keypair that
`fastapi_service` needs.

## Project status — read this before citing it as production-ready

**Verified working:** all services build and their code compiles; Django
and Alembic migrations were generated from the real models; the frontend
builds cleanly; the MCP tools register and `analyze_code` runs end-to-end;
the AST parser, RAG similarity ranking, and prompt templating all produce
correct output.

**Not yet verified:** the full stack has not been run end-to-end against a
live database with a real API key, so the complete
login → upload → generate cycle is untested in practice.

**Known gaps before this would be production-ready:**

- **No automated tests for this project itself** — the most notable gap
  given what the project does
- Refresh token is stored in `localStorage`; should be an `httpOnly`
  cookie set by Django
- No CI pipeline, error monitoring, or structured log aggregation
- No endpoint to list a user's past submissions (results are stored but
  never read back)
- Deep code parsing only supports Python; other languages return line
  counts only
- The bundled embedding model is a hashing trick for zero-setup local
  running, not a semantic model — swap it before relying on retrieval
  quality
