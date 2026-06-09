from typing import Dict, List
from datetime import date

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CompanyCount,
    DashboardTimelineResponse,
    TimelineDataPoint,
)
from app.models.job import JobStatus


class DashboardService:

    def __init__(self, repo: DashboardRepository):
        self.repo = repo

    def get_summary(self, user_id: str) -> DashboardSummaryResponse:
        """Calculate and return dashboard summary KPIs for the user."""
        # 1. Fetch status counts
        status_counts = self.repo.get_status_counts(user_id)
        
        # Initialize breakdown for all statuses with 0
        status_breakdown = {status.value: 0 for status in JobStatus}
        total_applications = 0
        offered_count = 0

        for status, count in status_counts:
            # SQLAlchemy might return string or Enum, handle both
            status_str = status.value if hasattr(status, "value") else str(status)
            status_breakdown[status_str] = count
            total_applications += count
            if status_str == JobStatus.offered.value:
                offered_count = count

        # 2. Compute Success Rate
        success_rate = 0.0
        if total_applications > 0:
            success_rate = round((offered_count / total_applications) * 100, 2)

        # 3. Compute Interview Rate
        interviewing_jobs_count = self.repo.get_interviewing_jobs_count(user_id)
        interview_rate = 0.0
        if total_applications > 0:
            interview_rate = round((interviewing_jobs_count / total_applications) * 100, 2)

        # 4. Fetch Active This Week Count
        active_this_week = self.repo.get_active_this_week_count(user_id)

        # 5. Fetch Top Companies
        top_companies_raw = self.repo.get_top_companies(user_id)
        top_companies = [
            CompanyCount(company=company, count=count)
            for company, count in top_companies_raw
        ]

        return DashboardSummaryResponse(
            total_applications=total_applications,
            success_rate=success_rate,
            interview_rate=interview_rate,
            active_this_week=active_this_week,
            status_breakdown=status_breakdown,
            top_companies=top_companies,
        )

    def get_timeline(self, user_id: str) -> DashboardTimelineResponse:
        """Calculate and return application timeline trends."""
        timeline_raw = self.repo.get_application_timeline(user_id)
        
        timeline = []
        for dt_val, count in timeline_raw:
            if dt_val is None:
                continue
            
            # Format the date cleanly as YYYY-MM-DD
            date_str = dt_val.strftime("%Y-%m-%d") if hasattr(dt_val, "strftime") else str(dt_val)
            timeline.append(TimelineDataPoint(date=date_str, count=count))

        return DashboardTimelineResponse(timeline=timeline)
