from typing import Optional

from app.models.interview import Interview, InterviewStatus
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.schemas.interview import InterviewCreateRequest, InterviewUpdateRequest


class InterviewService:

    def __init__(self, repo: InterviewRepository, job_repo: JobRepository):
        self.repo = repo
        self.job_repo = job_repo

    # ─── Create ───────────────────────────────────────────────────────────────

    def create_interview(
        self,
        job_id: str,
        user_id: str,
        data: InterviewCreateRequest,
    ) -> Interview:
        # Verify the job exists and belongs to this user
        job = self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise ValueError("Job not found")

        interview = Interview(
            job_id=job_id,
            user_id=user_id,
            round=data.round,
            interview_type=data.interview_type,
            scheduled_at=data.scheduled_at,
            status=data.status,
            interviewer_name=data.interviewer_name,
            location=data.location,
            meeting_link=data.meeting_link,
            feedback=data.feedback,
        )
        return self.repo.create(interview)

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_interview(self, interview_id: str, user_id: str) -> Interview:
        interview = self.repo.get_by_id(interview_id, user_id)
        if not interview:
            raise ValueError("Interview not found")
        return interview

    def list_by_job(
        self,
        job_id: str,
        user_id: str,
        status: Optional[InterviewStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Interview], int]:
        # Verify job ownership before listing
        job = self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise ValueError("Job not found")

        return self.repo.get_by_job(
            job_id=job_id,
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    def list_all(
        self,
        user_id: str,
        status: Optional[InterviewStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Interview], int]:
        return self.repo.get_all_for_user(
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    # ─── Update ───────────────────────────────────────────────────────────────

    def update_interview(
        self,
        interview_id: str,
        user_id: str,
        data: InterviewUpdateRequest,
    ) -> Interview:
        interview = self.get_interview(interview_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interview, field, value)

        return self.repo.save(interview)

    # ─── Delete ───────────────────────────────────────────────────────────────

    def delete_interview(self, interview_id: str, user_id: str) -> None:
        interview = self.get_interview(interview_id, user_id)
        self.repo.delete(interview)
