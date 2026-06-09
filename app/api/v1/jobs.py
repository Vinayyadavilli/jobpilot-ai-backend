from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.job import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobListResponse,
    JobStatusFilter,
)
from app.models.job import JobStatus, Job
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_service(db: Session) -> JobService:
    return JobService(JobRepository(db))


# ─── Create ───────────────────────────────────────────────────────────────────

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new job application."""
    job = _get_service(db).create_job(user_id=current_user.id, data=data)
    return job


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=JobListResponse)
def list_jobs(
    status: JobStatusFilter = Query(JobStatusFilter.all, description="Filter by status — use 'all' to return every job"),
    search: Optional[str] = Query(None, description="Search company, role, or location"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all job applications for the authenticated user.
    Supports filtering by status ('all' returns everything) and keyword search.
    """
    # Convert 'all' → None so the repository skips the status filter
    status_filter: Optional[JobStatus] = (
        None if status == JobStatusFilter.all
        else JobStatus(status.value)
    )

    jobs, total = _get_service(db).list_jobs(
        user_id=current_user.id,
        status=status_filter,
        search=search,
        skip=skip,
        limit=limit,
    )
    return JobListResponse(total=total, jobs=jobs)


# ─── Get Single ───────────────────────────────────────────────────────────────

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a single job application."""
    try:
        return _get_service(db).get_job(job_id=job_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ─── Update ───────────────────────────────────────────────────────────────────

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    data: JobUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Partially update a job application.
    Only provided fields are updated (PATCH semantics via exclude_unset).
    """
    try:
        return _get_service(db).update_job(
            job_id=job_id,
            user_id=current_user.id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a job application and all its interviews and notes."""
    try:
        _get_service(db).delete_job(job_id=job_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
