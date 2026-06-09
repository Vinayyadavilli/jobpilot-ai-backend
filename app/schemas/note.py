from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─── Request Schemas ──────────────────────────────────────────────────────────

class NoteCreateRequest(BaseModel):
    content: str


class NoteUpdateRequest(BaseModel):
    content: str


# ─── Response Schemas ─────────────────────────────────────────────────────────

class NoteResponse(BaseModel):
    id: str
    job_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    total: int
    notes: list[NoteResponse]
