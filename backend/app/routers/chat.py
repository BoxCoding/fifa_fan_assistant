"""Chat endpoint — the multi-persona assistant flow (English)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.agent import handle_chat
from app.core.auth import can_access, get_current_user
from app.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])

ROLES = [
    {"id": "fan", "name": "Fan", "blurb": "Navigation, food, crowds, transport & accessibility"},
    {"id": "volunteer", "name": "Volunteer", "blurb": "Procedures, task assignments & fan support"},
    {"id": "staff", "name": "Venue Staff", "blurb": "Live incidents, response SOPs & crowd control"},
    {"id": "organizer", "name": "Organizer", "blurb": "Operational briefings & real-time decisions"},
]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, payload: dict = Depends(get_current_user)) -> ChatResponse:
    # Authorization: you may only converse in a persona your account can access.
    if not can_access(payload.get("role", "fan"), req.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account is not authorized for the '{req.role}' persona.",
        )
    return await handle_chat(req.message, req.role, req.stadium_id, req.history)


@router.get("/roles")
async def roles() -> dict:
    return {"roles": ROLES}
