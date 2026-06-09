from sqlalchemy.orm import Session
from typing import Optional

from app.models.interview import Interview, InterviewStatus


class InterviewRepository:

    def __init__(self, db: Session):
        self.db = db

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_by_id(self, interview_id: str, user_id: str) -> Interview | None:
        """Fetch a single interview owned by the given user."""
        return (
            self.db.query(Interview)
            .filter(Interview.id == interview_id, Interview.user_id == user_id)
            .first()
        )

    def get_by_job(
        self,
        job_id: str,
        user_id: str,
        status: Optional[InterviewStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Interview], int]:
        """
        List all interviews for a specific job.
        Optionally filter by status. Returns (items, total_count).
        """
        query = (
            self.db.query(Interview)
            .filter(Interview.job_id == job_id, Interview.user_id == user_id)
        )

        if status:
            query = query.filter(Interview.status == status)

        total = query.count()
        items = (
            query
            .order_by(Interview.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def get_all_for_user(
        self,
        user_id: str,
        status: Optional[InterviewStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Interview], int]:
        """List all interviews across all jobs for a user."""
        query = self.db.query(Interview).filter(Interview.user_id == user_id)

        if status:
            query = query.filter(Interview.status == status)

        total = query.count()
        items = (
            query
            .order_by(Interview.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    # ─── Write ────────────────────────────────────────────────────────────────

    def create(self, interview: Interview) -> Interview:
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def save(self, interview: Interview) -> Interview:
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def delete(self, interview: Interview) -> None:
        self.db.delete(interview)
        self.db.commit()
