from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

from app.models.interview import InterviewType, InterviewStatus


# ─── Filter Enum (includes 'all' for list endpoint) ───────────────────────────

class InterviewStatusFilter(str, enum.Enum):
    all         = "all"
    scheduled   = "scheduled"
    completed   = "completed"
    cancelled   = "cancelled"
    rescheduled = "rescheduled"


# ─── Request Schemas ──────────────────────────────────────────────────────────

class InterviewCreateRequest(BaseModel):
    round: Optional[str] = None
    interview_type: InterviewType = InterviewType.video
    scheduled_at: Optional[datetime] = None
    status: InterviewStatus = InterviewStatus.scheduled
    interviewer_name: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    feedback: Optional[str] = None


class InterviewUpdateRequest(BaseModel):
    round: Optional[str] = None
    interview_type: Optional[InterviewType] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[InterviewStatus] = None
    interviewer_name: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    feedback: Optional[str] = None


# ─── Response Schemas ─────────────────────────────────────────────────────────

class InterviewResponse(BaseModel):
    id: str
    job_id: str
    user_id: str
    round: Optional[str] = None
    interview_type: InterviewType
    scheduled_at: Optional[datetime] = None
    status: InterviewStatus
    interviewer_name: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewListResponse(BaseModel):
    total: int
    interviews: list[InterviewResponse]
