from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import enum

from app.models.job import JobStatus


class JobStatusFilter(str, enum.Enum):
    """Used only for list filtering — includes 'all' on top of the stored statuses."""
    all          = "all"
    applied      = "applied"
    interviewing = "interviewing"
    offered      = "offered"
    rejected     = "rejected"
    withdrawn    = "withdrawn"


# ─── Request Schemas ──────────────────────────────────────────────────────────

class JobCreateRequest(BaseModel):
    company: str
    role: str
    status: JobStatus = JobStatus.applied
    source: Optional[str] = None
    applied_date: Optional[date] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    description: Optional[str] = None


class JobUpdateRequest(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[JobStatus] = None
    source: Optional[str] = None
    applied_date: Optional[date] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    description: Optional[str] = None


# ─── Response Schemas ─────────────────────────────────────────────────────────

class JobResponse(BaseModel):
    id: str
    user_id: str
    company: str
    role: str
    status: JobStatus
    source: Optional[str] = None
    applied_date: Optional[date] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    total: int
    jobs: list[JobResponse]
