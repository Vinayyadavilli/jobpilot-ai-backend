from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, Date
from datetime import datetime, timedelta
from typing import List, Tuple, Any

from app.models.job import Job, JobStatus
from app.models.interview import Interview


class DashboardRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_status_counts(self, user_id: str) -> List[Tuple[JobStatus, int]]:
        """Get count of jobs grouped by status for a given user."""
        results = (
            self.db.query(Job.status, func.count(Job.id))
            .filter(Job.user_id == user_id)
            .group_by(Job.status)
            .all()
        )
        return [(status, count) for status, count in results]

    def get_active_this_week_count(self, user_id: str) -> int:
        """Count jobs applied or created within the last 7 days."""
        seven_days_ago_date = datetime.utcnow().date() - timedelta(days=7)
        seven_days_ago_datetime = datetime.utcnow() - timedelta(days=7)

        return (
            self.db.query(func.count(Job.id))
            .filter(
                Job.user_id == user_id,
                or_(
                    Job.applied_date >= seven_days_ago_date,
                    and_(Job.applied_date == None, Job.created_at >= seven_days_ago_datetime)
                )
            )
            .scalar() or 0
        )

    def get_top_companies(self, user_id: str, limit: int = 5) -> List[Tuple[str, int]]:
        """Get top applied companies with application count."""
        results = (
            self.db.query(Job.company, func.count(Job.id))
            .filter(Job.user_id == user_id)
            .group_by(Job.company)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
            .all()
        )
        return [(company, count) for company, count in results]

    def get_interviewing_jobs_count(self, user_id: str) -> int:
        """Count jobs with status 'interviewing' or having at least one scheduled/completed interview."""
        return (
            self.db.query(func.count(Job.id))
            .filter(
                Job.user_id == user_id,
                or_(
                    Job.status == JobStatus.interviewing,
                    Job.id.in_(
                        self.db.query(Interview.job_id).filter(Interview.user_id == user_id)
                    )
                )
            )
            .scalar() or 0
        )

    def get_application_timeline(self, user_id: str) -> List[Tuple[Any, int]]:
        """Get timeline of job counts grouped by date (YYYY-MM-DD)."""
        results = (
            self.db.query(
                func.coalesce(Job.applied_date, func.cast(Job.created_at, Date)).label("date_group"),
                func.count(Job.id)
            )
            .filter(Job.user_id == user_id)
            .group_by("date_group")
            .order_by("date_group")
            .all()
        )
        return [(date_group, count) for date_group, count in results]
