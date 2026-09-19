import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import JWT_ALGORITHM, JWT_PUBLIC_KEY

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: int
    username: str
    role: str


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid access token")


def verify_token_string(token: str) -> CurrentUser:
    """
    Same verification as get_current_user, but callable outside of FastAPI's
    dependency injection — used by the MCP server, which has no HTTP request
    to attach a Depends() to but still needs the same identity guarantees.
    """
    payload = _decode_token(token)
    return CurrentUser(
        user_id=payload["user_id"],
        username=payload.get("username", ""),
        role=payload.get("role", "developer"),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Verifies the token's RS256 signature locally — no call back to Django.
    Django is the only service that can mint a token that passes this check.
    """
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    return verify_token_string(credentials.credentials)


def require_role(*allowed_roles: str):
    """Dependency factory for endpoints that need role-based access control."""

    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return _checker
