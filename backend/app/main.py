"""Kickoff — FIFA World Cup 2026 stadium-operations & fan-experience API.

Run:  uvicorn app.main:app --reload --port 8090
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core import cache, httpclient
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.llm import health as llm_health
from app.routers import auth, chat, ops, stadium, transport


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Release pooled outbound connections cleanly on shutdown.
    await httpclient.aclose()


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)

# gzip responses over ~500 bytes (efficiency: smaller payloads on the wire).
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public: auth (login) + health/root below.
app.include_router(auth.router)

# Protected: every app-facing router requires a valid Bearer token.
_protected = [Depends(get_current_user)]
app.include_router(chat.router, dependencies=_protected)
app.include_router(stadium.router, dependencies=_protected)
app.include_router(transport.router, dependencies=_protected)
app.include_router(ops.router, dependencies=_protected)


@app.get("/")
async def root() -> dict:
    return {"app": settings.APP_NAME, "version": settings.VERSION, "docs": "/docs"}


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "demo_mode": settings.DEMO_MODE,
        "llm": await llm_health(),
        "cache": cache.stats(),
    }
