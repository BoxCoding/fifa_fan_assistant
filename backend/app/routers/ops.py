"""Operational-intelligence endpoints for staff and organizers.

Powers the staff incident console and the organizer dashboard: live incidents,
a synthesised operational briefing, volunteer task lists, SOP lookup, and
sustainability KPIs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.agent import operational_briefing
from app.core.auth import require_role
from app.data import ops
from app.data.incidents import live_incidents
from app.data.procedures import PROCEDURES, find_procedure
from app.data.stadiums import get_venue
from app.data.sustainability import sustainability_snapshot

router = APIRouter(prefix="/api", tags=["operations"])

# Reusable authorization dependencies.
_staff = Depends(require_role("staff"))
_volunteer = Depends(require_role("volunteer"))


@router.get("/incidents/{stadium_id}")
async def incidents(stadium_id: str, _: dict = _staff) -> dict:
    if not get_venue(stadium_id):
        raise HTTPException(status_code=404, detail="Unknown stadium")
    return live_incidents()


@router.get("/ops/briefing/{stadium_id}")
async def briefing(stadium_id: str, _: dict = _staff) -> dict:
    if not get_venue(stadium_id):
        raise HTTPException(status_code=404, detail="Unknown stadium")
    return await operational_briefing(stadium_id)


@router.get("/volunteer/tasks")
async def volunteer_tasks(_: dict = _volunteer) -> dict:
    return ops.volunteer_tasks()


@router.get("/procedures")
async def procedures(role: str | None = Query(None), q: str | None = Query(None), _: dict = _volunteer) -> dict:
    if q:
        return {"procedures": find_procedure(q, role)}
    items = PROCEDURES if not role else [p for p in PROCEDURES if role in p["roles"]]
    return {"procedures": items}


@router.get("/sustainability/{stadium_id}")
async def sustainability(stadium_id: str, _: dict = _staff) -> dict:
    if not get_venue(stadium_id):
        raise HTTPException(status_code=404, detail="Unknown stadium")
    return sustainability_snapshot()
