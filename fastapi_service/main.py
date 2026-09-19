import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import CORS_ALLOWED_ORIGINS
from app.core.logging import get_logger, setup_logging
from app.core.rate_limiter import limiter

setup_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic ("alembic upgrade head"), not create_all —
    # having both meant the migration history could silently diverge from
    # what was actually in the database.
    logger.info("fastapi_service_started")
    yield
    logger.info("fastapi_service_stopped")


app = FastAPI(title="Test Case Generator - Core Service", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Same correlation-id pattern as the Django service, so a request
    can be traced across both services by its X-Request-ID."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.monotonic()

    response = await call_next(request)

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id, request.method, request.url.path, response.status_code, duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
