"""Pydantic request/response schemas shared across routers."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
# The four personas the platform serves. Each gets a tailored assistant.
Role = Literal["fan", "volunteer", "staff", "organizer"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message / question (English).")
    role: Role = Field("fan", description="Persona asking: fan, volunteer, staff, or organizer.")
    stadium_id: str = Field("metlife", description="Stadium context for the query.")
    history: list[ChatMessage] = Field(default_factory=list)


class Action(BaseModel):
    """A suggested follow-up the UI can render as a tappable chip."""

    label: str
    query: str


class ChatResponse(BaseModel):
    reply: str
    role: Role
    intent: str
    source: Literal["llm", "fallback"]
    cached: bool = False
    actions: list[Action] = Field(default_factory=list)
    data: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class UserOut(BaseModel):
    username: str
    role: Role
    name: str


class LoginResponse(BaseModel):
    token: str
    expires_at: int
    user: UserOut


# ---------------------------------------------------------------------------
# Stadium / navigation
# ---------------------------------------------------------------------------
class NavigationRequest(BaseModel):
    stadium_id: str = "metlife"
    from_point: str = Field(..., description="Current location, e.g. 'Gate A' or 'Section 112'.")
    to_point: str = Field(..., description="Destination, e.g. 'Section 232' or 'nearest restroom'.")
    accessible: bool = Field(False, description="Require step-free / accessible routing.")


class CrowdRequest(BaseModel):
    stadium_id: str = "metlife"
