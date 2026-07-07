"""Authentication endpoints: login and current-user."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core import ratelimit
from app.core.auth import authenticate, get_current_user, get_user_record
from app.core.config import settings
from app.core.security import create_token
from app.models import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    # Vercel/other proxies set X-Forwarded-For; take the first hop.
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request) -> LoginResponse:
    ip = _client_ip(request)
    if not ratelimit.check(f"login:{ip}", settings.LOGIN_RATE_LIMIT, settings.LOGIN_RATE_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again shortly.",
        )
    user = authenticate(req.username, req.password)
    if user is None:
        # Generic message — do not reveal whether the username exists.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token, exp = create_token(user["username"], user["role"])
    return LoginResponse(token=token, expires_at=exp, user=UserOut(**user))


@router.get("/me", response_model=UserOut)
async def me(payload: dict = Depends(get_current_user)) -> UserOut:
    username = payload["sub"]
    record = get_user_record(username) or {}
    return UserOut(username=username, role=payload["role"], name=record.get("name", username))
