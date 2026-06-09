from typing import Optional

from app.models.job import Job, JobStatus
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreateRequest, JobUpdateRequest


class JobService:

    def __init__(self, repo: JobRepository):
        self.repo = repo

    # ─── Create ───────────────────────────────────────────────────────────────

    def create_job(self, user_id: str, data: JobCreateRequest) -> Job:
        job = Job(
            user_id=user_id,
            company=data.company,
            role=data.role,
            status=data.status,
            source=data.source,
            applied_date=data.applied_date,
            job_url=data.job_url,
            location=data.location,
            salary_range=data.salary_range,
            description=data.description,
        )
        return self.repo.create(job)

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_job(self, job_id: str, user_id: str) -> Job:
        job = self.repo.get_by_id(job_id, user_id)
        if not job:
            raise ValueError("Job not found")
        return job

    def list_jobs(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Job], int]:
        return self.repo.get_all(
            user_id=user_id,
            status=status,
            search=search,
            skip=skip,
            limit=limit,
        )

    # ─── Update ───────────────────────────────────────────────────────────────

    def update_job(self, job_id: str, user_id: str, data: JobUpdateRequest) -> Job:
        job = self.get_job(job_id, user_id)

        # Only update fields that were explicitly provided (not None)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        return self.repo.save(job)

    # ─── Delete ───────────────────────────────────────────────────────────────

    def delete_job(self, job_id: str, user_id: str) -> None:
        job = self.get_job(job_id, user_id)
        self.repo.delete(job)
