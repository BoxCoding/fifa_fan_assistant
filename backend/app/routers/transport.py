"""Live transportation intelligence endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data import live
from app.data.stadiums import get_venue

router = APIRouter(prefix="/api", tags=["transport"])


@router.get("/transport/{stadium_id}")
async def transport(stadium_id: str) -> dict:
    if not get_venue(stadium_id):
        raise HTTPException(status_code=404, detail="Unknown stadium")
    return live.transport_snapshot()
