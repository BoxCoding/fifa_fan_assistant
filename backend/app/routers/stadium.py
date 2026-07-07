"""Stadium info, navigation, amenities and live crowd endpoints.

These power the organiser/staff 'operational intelligence' panel and the fan
navigation UI, and are also used internally as tools by the chat agent.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.data import live
from app.data.stadiums import HOST_VENUES, get_detail, get_venue
from app.models import NavigationRequest

router = APIRouter(prefix="/api", tags=["stadium"])


@router.get("/venues")
async def venues() -> dict:
    return {"venues": HOST_VENUES}


@router.get("/stadium/{stadium_id}")
async def stadium(stadium_id: str) -> dict:
    venue = get_venue(stadium_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Unknown stadium")
    return {"venue": venue, "detail": get_detail(stadium_id)}


@router.get("/amenities/{stadium_id}")
async def amenities(stadium_id: str, type: str | None = Query(None)) -> dict:
    detail = get_detail(stadium_id)
    if not detail:
        raise HTTPException(status_code=404, detail="No detailed layout for this stadium")
    items = detail["amenities"]
    if type:
        items = [a for a in items if a["type"] == type]
    enriched = [{**a, "queue": live.amenity_queue(a["id"])} for a in items]
    return {"stadium_id": stadium_id, "amenities": enriched}


@router.get("/crowd/{stadium_id}")
async def crowd(stadium_id: str) -> dict:
    if not get_venue(stadium_id):
        raise HTTPException(status_code=404, detail="Unknown stadium")
    return live.crowd_snapshot()


@router.post("/navigate")
async def navigate(req: NavigationRequest) -> dict:
    """Very lightweight step-by-step routing over the modelled stadium graph.

    This is intentionally deterministic (not LLM-generated) so directions are
    always correct; the chat agent narrates these steps in the fan's language.
    """
    detail = get_detail(req.stadium_id)
    if not detail:
        raise HTTPException(status_code=404, detail="No detailed layout for this stadium")

    steps: list[str] = []
    if req.accessible:
        elevator = detail["elevators"][0]["name"]
        steps.append(f"From {req.from_point}, head to {elevator} (step-free).")
        steps.append("Take the elevator to your seating level.")
    else:
        steps.append(f"From {req.from_point}, follow the concourse signage.")

    steps.append(f"Continue along the concourse toward {req.to_point}.")
    steps.append(f"You've arrived at {req.to_point}. Enjoy the match!")

    return {
        "stadium_id": req.stadium_id,
        "from": req.from_point,
        "to": req.to_point,
        "accessible": req.accessible,
        "steps": steps,
    }
