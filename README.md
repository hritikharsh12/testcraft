Testcraft — AI Test Case Generator

Upload a source file, get back generated unit tests and concrete improvement suggestions. A full-stack system built to demonstrate production patterns: JWT auth with refresh rotation, RAG-augmented LLM generation, an MCP server, and a containerized multi-service architecture.

Features
Upload & analyze — drop in a .py file, get back an AST-based structural report: functions, classes, line numbers, missing-docstring warnings
Generate tests — retrieval-augmented prompting pulls relevant testing conventions from a knowledge base, then an LLM generates a runnable pytest file plus specific improvement suggestions
JWT auth with rotation — RS256-signed access/refresh tokens; every refresh invalidates the previous one
MCP server — the same pipeline exposed as MCP tools (analyze_code, generate_tests, suggest_improvements), so any MCP-compatible client can call it directly
Swappable LLM provider — runs on Groq (free tier, open-weight models) by default, or Anthropic's Claude with one env var change
Architecture
Service	Port	Responsibility
auth (Django + DRF)	8000	Users, JWT issuance/refresh/rotation, sessions, admin
api (FastAPI)	8001	Upload, AST parsing, RAG retrieval, prompt building, LLM calls
frontend (React + Vite)	5173	Upload UI, structure report, generated test viewer
postgres	5432	Submissions, results, RAG knowledge base
redis	6379	Rate limiting, session cache

FastAPI verifies Django-issued JWTs using only the public RS256 key — it can authenticate users but can never mint tokens itself.

Client ──▶ Django (auth, JWT) ──▶ FastAPI (upload, parse, RAG, LLM) ──▶ Postgres / Redis
                                        │
                                        └──▶ MCP server (same pipeline, direct tool calls)
Tech stack

Backend: Django 5, Django REST Framework, SimpleJWT, FastAPI, SQLAlchemy (async), Alembic, PostgreSQL, Redis, Jinja2 AI/LLM: Groq / Anthropic Claude, custom RAG pipeline (hashing-based embeddings + cosine similarity), MCP (Model Context Protocol) Frontend: React 18, Vite, React Router Infra: Docker, Docker Compose

Quick start
bash
cp .env.example .env
# edit .env — set GROQ_API_KEY (free at console.groq.com/keys, no credit card)
docker compose up --build

Open http://localhost:5173, register an account, upload a .py file, click "Generate tests."

Compose handles everything: generates the RS256 keypair on first boot, waits for Postgres/Redis health checks, runs both migration systems (Django + Alembic), seeds the RAG knowledge base, and creates an admin user from your .env values.

Manual setup (without Docker)

See the README in each service directory (django_auth_service/, fastapi_service/, frontend/). Start Django first — it generates the RS256 keypair that FastAPI needs to verify tokens.

API endpoints

Auth (Django, :8000)

Method	Path	Purpose
POST	/auth/register/	Create a user
POST	/auth/login/	Get access + refresh tokens
POST	/auth/refresh/	Rotate tokens
POST	/auth/logout/	Blacklist a refresh token
GET	/auth/me/	Current user profile

Core (FastAPI, :8001)

Method	Path	Purpose
POST	/api/v1/upload	Upload + parse a code file
POST	/api/v1/generate/{submission_id}	Run RAG + LLM, get tests + suggestions
Known limitations

Built and debugged incrementally with real end-to-end testing rather than left unverified — see Debugging Journey below for what that process actually looked like. Honest gaps that remain:

No automated test suite for this project itself
Refresh token stored in localStorage on the frontend; a production deployment should use an httpOnly cookie set directly by Django instead
Deep AST parsing only covers Python; other languages get line-count-only analysis
The default embedding model (HashingEmbedder) is a dependency-free keyword-overlap approximation, not a true semantic embedding — swap in a hosted model before relying on retrieval quality at scale
Groq's free tier means generation quality depends on an open-weight model rather than Claude; switch LLM_PROVIDER=anthropic once billing is set up for higher-quality output
Debugging journey

This system was built service-by-service and tested against real infrastructure rather than assumed to work — which surfaced (and fixed) several genuine bugs along the way:

Missing dependencies caught at Docker build time: alembic absent from fastapi_service/requirements.txt, redis absent from django_auth_service/requirements.txt (needed for the session cache backend) — both would have crashed the containers on first boot.
A CORS/exception-handling bug: unhandled exceptions from the LLM provider's SDK were escaping past FastAPI's error handling, which meant the response left the server with no CORS headers attached. The browser reported this as an opaque "Failed to fetch" instead of a real error. Fixed by explicitly catching each SDK exception type and adding a catch-all handler that manually attaches CORS headers.
A dependency version conflict: openai==1.35.0 (used for Groq's OpenAI-compatible endpoint) broke against a newer httpx that removed an argument the old SDK still passed. Fixed by upgrading to a version that no longer depends on httpx directly.
A retired model: llama-3.3-70b-versatile moved to Groq's enterprise-only tier after this was originally built. Diagnosed by querying Groq's own /models endpoint directly rather than trusting stale documentation, and switching to openai/gpt-oss-20b.
A swallowed validation error: the frontend only checked for DRF's {"detail": "..."} error shape, so registration failures (like a duplicate username) surfaced as a generic "Request failed (400)" instead of the actual reason. Fixed by also parsing DRF's per-field validation error format.
Project structure
testcraft/
├── docker-compose.yml
├── django_auth_service/     # Auth: JWT, sessions, admin
├── fastapi_service/         # Core: upload, RAG, LLM, MCP server
└── frontend/                # React + Vite UI
