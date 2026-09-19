# FastAPI core service

Handles code upload, parsing, and (in later steps) the RAG + prompt + LLM
pipeline. Trusts identity entirely to the Django auth service — it verifies
JWTs locally using Django's public key and never calls back to Django.

## Setup

```bash
cd fastapi_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # edit DATABASE_URL / REDIS_URL if needed

# copy the PUBLIC key only from the Django service — never the private key
cp ../django_auth_service/core/keys/public.pem keys/public.pem

uvicorn main:app --reload --port 8001
```

Postgres and Redis must be running and reachable per `.env`. Apply the
Alembic migration before starting the app:

```bash
alembic upgrade head
```

(`main.py`'s `create_all` on startup is still there as a dev convenience —
harmless once the migration has also run, since `create_all` skips tables
that already exist — but the migration is the source of truth going
forward. Generate new migrations after model changes with
`alembic revision --autogenerate -m "description"`.)

## Endpoints

| Method | Path              | Auth   | Purpose                                      |
|--------|-------------------|--------|-----------------------------------------------|
| GET    | `/health`         | none   | Liveness check                                |
| POST   | `/api/v1/upload`  | Bearer | Upload a code file, get back a parsed summary |
| POST   | `/api/v1/generate/{submission_id}` | Bearer | Run RAG + LLM to generate tests + suggestions |

Before calling `/generate`, seed the knowledge base once:

```bash
python -m app.services.rag.seed
```

## Example flow

```bash
# access token comes from the Django service's /auth/login/
curl -X POST localhost:8001/api/v1/upload \
  -H "Authorization: Bearer <access>" \
  -F "file=@example.py"
```

Response:
```json
{
  "submission_id": 1,
  "filename": "example.py",
  "language": "python",
  "summary": {
    "language": "python",
    "line_count": 42,
    "functions": [{"name": "add", "line_number": 3, "args": ["a", "b"], "has_docstring": false, "is_async": false}],
    "classes": [],
    "imports": ["os"],
    "warnings": ["1 function(s) missing docstrings: add"]
  },
  "created_at": "2026-07-29T12:00:00Z"
}
```

`submission_id` is what the next stage (RAG + prompt building + LLM call)
will take as input to actually generate tests and suggestions.

```bash
curl -X POST localhost:8001/api/v1/generate/1 -H "Authorization: Bearer <access>"
```

Response:
```json
{
  "submission_id": 1,
  "generated_tests": "import pytest\nfrom example import add\n\ndef test_add_positive():\n    assert add(2, 3) == 5\n...",
  "suggestions": ["Add a docstring to add()", "Handle non-numeric input explicitly"],
  "model_used": "claude-sonnet-5",
  "created_at": "2026-07-29T12:05:00Z"
}
```

### How generation actually works

1. Build a retrieval query from the submission's language + function names.
2. `retrieve_context` embeds that query and ranks knowledge-base chunks by
   cosine similarity — testing conventions relevant to this code, not the
   whole corpus.
3. `build_prompt` renders `test_gen.jinja` with the source code, retrieved
   conventions, and static-analysis warnings baked in.
4. `generate_tests_and_suggestions` sends that prompt to Claude and parses
   the strict JSON response.
5. Result is persisted to `test_generation_results` and returned.

## MCP server

The same pipeline is also exposed as an MCP server — `analyze_code`,
`generate_tests`, and `suggest_improvements` call the exact same service
functions the REST API uses, so an MCP client gets identical behavior
instead of a parallel reimplementation.

```bash
python -m app.services.mcp.server
```

This runs over stdio by default. Example Claude Desktop config entry:

```json
"test-case-generator": {
  "command": "python",
  "args": ["-m", "app.services.mcp.server"],
  "cwd": "/absolute/path/to/fastapi_service"
}
```

`generate_tests` and `suggest_improvements` take `access_token` as a plain
argument (there's no HTTP header to piggyback on in MCP), verified the
same way the REST API verifies it, and rate-limited per user via a plain
Redis fixed-window counter (`core/rate_limiter.check_rate_limit`) since
`slowapi`'s decorator only works on HTTP routes. `analyze_code` needs no
token — it's pure static analysis with nothing persisted.

## What's deliberately industrial here, and why

- **Stateless auth verification** — this service can scale horizontally
  with zero coordination with Django; every instance verifies tokens
  independently from the same public key.
- **Per-user rate limiting via the token itself**, not just IP — so it
  survives users behind shared NAT/corporate proxies and can't be
  bypassed by rotating IPs.
- **Strict upload validation** — extension allowlist, size cap, and a
  UTF-8 decode check before anything touches the parser or the DB.
- **Correlation id propagation** — the same `X-Request-ID` header pattern
  as the Django service, so one request's logs can be traced across
  both services.
- **Parser output is a stable Pydantic contract** (`ParsedSummary`) —
  the RAG/prompt stage coming next consumes this shape regardless of
  which language-specific parser produced it.
- **Embedding client is an abstract interface** — the shipped
  `HashingEmbedder` needs no external API key so the whole pipeline runs
  locally out of the box; swap in a hosted embedding model for production
  semantic quality without touching the retriever or anything above it.
- **Prompts live in `.jinja` files, not Python strings** — non-engineers
  can tune wording, and diffs on prompt changes are readable in review.
- **The LLM call is isolated to one narrow function** — retries, model
  swaps, or moving to streaming responses later only touches
  `llm_client.py`.
- **Tighter rate limit on `/generate` than `/upload`** — LLM calls cost
  real money and latency, so they're throttled harder than a plain upload.
- **MCP tools call the same service functions as the REST endpoints**,
  not a reimplementation — `app/services/mcp/tools.py` imports the exact
  parser, retriever, prompt builder, and LLM client the FastAPI routes use.
  The two entry points can never silently drift apart in behavior.
