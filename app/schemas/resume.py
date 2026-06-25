from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class EnhanceUrlRequest(BaseModel):
    url: str


class ResumeResponse(BaseModel):
    id: str
    original_url: Optional[str] = None
    raw_text: str
    enhanced_text: str
    download_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    total: int
    resumes: List[ResumeResponse]
