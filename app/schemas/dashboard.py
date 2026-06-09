from pydantic import BaseModel
from typing import List, Dict


class CompanyCount(BaseModel):
    company: str
    count: int


class DashboardSummaryResponse(BaseModel):
    total_applications: int
    success_rate: float
    interview_rate: float
    active_this_week: int
    status_breakdown: Dict[str, int]
    top_companies: List[CompanyCount]


class TimelineDataPoint(BaseModel):
    date: str
    count: int


class DashboardTimelineResponse(BaseModel):
    timeline: List[TimelineDataPoint]
