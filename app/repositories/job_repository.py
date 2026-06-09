from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.models.job import Job, JobStatus


class JobRepository:

    def __init__(self, db: Session):
        self.db = db

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_by_id(self, job_id: str, user_id: str) -> Job | None:
        """Fetch a single job owned by the given user."""
        return (
            self.db.query(Job)
            .filter(Job.id == job_id, Job.user_id == user_id)
            .first()
        )

    def get_all(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Job], int]:
        """
        List jobs for a user with optional status filter and keyword search
        across company + role. Returns (items, total_count).
        """
        query = self.db.query(Job).filter(Job.user_id == user_id)

        if status:
            query = query.filter(Job.status == status)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Job.company.ilike(term),
                    Job.role.ilike(term),
                    Job.location.ilike(term),
                )
            )

        total = query.count()
        items = (
            query
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    # ─── Write ────────────────────────────────────────────────────────────────

    def create(self, job: Job) -> Job:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def save(self, job: Job) -> Job:
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job: Job) -> None:
        self.db.delete(job)
        self.db.commit()
