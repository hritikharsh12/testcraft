import jwt
from slowapi import Limiter
from starlette.requests import Request

from app.core.config import JWT_ALGORITHM, JWT_PUBLIC_KEY, REDIS_URL


def _rate_limit_key(request: Request) -> str:
    """
    Key by authenticated user id when a valid token is present, so one
    user's usage can't starve another's. Falls back to client IP for
    unauthenticated requests (e.g. hitting a public endpoint).
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
            return f"user:{payload['user_id']}"
        except jwt.InvalidTokenError:
            pass  # falls through to IP-based limiting; auth dependency will reject it anyway
    return f"ip:{request.client.host}"


limiter = Limiter(key_func=_rate_limit_key, storage_uri=REDIS_URL)


_redis_client = None


def _get_redis():
    import redis.asyncio as aioredis
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
    """
    Fixed-window counter for callers with no HTTP request to hang a
    slowapi decorator off of — namely the MCP server, which invokes the
    same generation pipeline as the REST API but as direct tool calls.
    Returns True if this call is within the limit, False if it should
    be rejected.
    """
    redis_client = _get_redis()
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window_seconds)
    return current <= max_calls
