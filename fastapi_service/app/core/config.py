from pathlib import Path
 
from decouple import Csv, config
 
BASE_DIR = Path(__file__).resolve().parent.parent.parent
 
# The RS256 public key Django signed tokens with. This service never sees
# the private key, so it can verify identity but can never mint tokens.
JWT_PUBLIC_KEY = (BASE_DIR / "keys" / "public.pem").read_text()
JWT_ALGORITHM = "RS256"
 
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/2")
 
DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql+asyncpg://postgres:postgres@localhost:5432/testcasegen",
)
 
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:3000", cast=Csv()
)
 
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE_BYTES = config("MAX_UPLOAD_SIZE_BYTES", default=2 * 1024 * 1024, cast=int)  # 2 MB
ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go"}
 
LOG_FILE = BASE_DIR / "logs" / "fastapi_service.log"
 
# LLM provider — swap ANTHROPIC_MODEL for whatever's current; check
# docs.claude.com for the latest model names rather than hardcoding trust
# in any one string long-term.
#
# LLM_PROVIDER picks which backend generate.py actually calls. "groq" is
# a genuinely free, no-credit-card option (rate-limited, open-weight
# models) — a reasonable default for local development and demos.
# Switch to "anthropic" once billing is set up, without touching any
# code above llm_client.py.
LLM_PROVIDER = config("LLM_PROVIDER", default="groq")
 
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-sonnet-5")
 
GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.3-70b-versatile")
 
RAG_TOP_K = config("RAG_TOP_K", default=3, cast=int)
EMBEDDING_DIM = config("EMBEDDING_DIM", default=256, cast=int)
 
# MCP tool calls aren't HTTP requests, so they use the plain Redis
# fixed-window limiter (see core/rate_limiter.check_rate_limit) instead
# of slowapi's per-route decorator.
MCP_GENERATE_RATE_LIMIT = config("MCP_GENERATE_RATE_LIMIT", default=5, cast=int)
MCP_RATE_LIMIT_WINDOW_SECONDS = config("MCP_RATE_LIMIT_WINDOW_SECONDS", default=60, cast=int)