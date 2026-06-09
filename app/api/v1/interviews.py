from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.interview import (
    InterviewCreateRequest,
    InterviewUpdateRequest,
    InterviewResponse,
    InterviewListResponse,
    InterviewStatusFilter,
)
from app.models.interview import InterviewStatus
from app.models.user import User
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.services.interview_service import InterviewService

router = APIRouter(tags=["Interviews"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_service(db: Session) -> InterviewService:
    return InterviewService(
        repo=InterviewRepository(db),
        job_repo=JobRepository(db),
    )


def _resolve_status(filter_val: InterviewStatusFilter) -> Optional[InterviewStatus]:
    """Convert 'all' → None so the repository skips the status filter."""
    if filter_val == InterviewStatusFilter.all:
        return None
    return InterviewStatus(filter_val.value)


# ═══════════════════════════════════════════════════════════════════════════════
# Nested routes:  /jobs/{job_id}/interviews
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/jobs/{job_id}/interviews",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interview(
    job_id: str,
    data: InterviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedule a new interview for a specific job."""
    try:
        return _get_service(db).create_interview(
            job_id=job_id,
            user_id=current_user.id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/jobs/{job_id}/interviews",
    response_model=InterviewListResponse,
)
def list_interviews_by_job(
    job_id: str,
    status: InterviewStatusFilter = Query(
        InterviewStatusFilter.all,
        description="Filter by status — 'all' returns every interview for this job",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all interviews for a specific job application."""
    try:
        interviews, total = _get_service(db).list_by_job(
            job_id=job_id,
            user_id=current_user.id,
            status=_resolve_status(status),
            skip=skip,
            limit=limit,
        )
        return InterviewListResponse(total=total, interviews=interviews)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Flat routes:  /interviews
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/interviews",
    response_model=InterviewListResponse,
)
def list_all_interviews(
    status: InterviewStatusFilter = Query(
        InterviewStatusFilter.all,
        description="Filter by status across all jobs — 'all' returns everything",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all interviews across every job for the authenticated user."""
    interviews, total = _get_service(db).list_all(
        user_id=current_user.id,
        status=_resolve_status(status),
        skip=skip,
        limit=limit,
    )
    return InterviewListResponse(total=total, interviews=interviews)


@router.get(
    "/interviews/{interview_id}",
    response_model=InterviewResponse,
)
def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a single interview."""
    try:
        return _get_service(db).get_interview(
            interview_id=interview_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/interviews/{interview_id}",
    response_model=InterviewResponse,
)
def update_interview(
    interview_id: str,
    data: InterviewUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an interview.
    Only provided fields are changed (partial update).
    """
    try:
        return _get_service(db).update_interview(
            interview_id=interview_id,
            user_id=current_user.id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/interviews/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an interview."""
    try:
        _get_service(db).delete_interview(
            interview_id=interview_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
