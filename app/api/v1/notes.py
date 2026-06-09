from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.note import (
    NoteCreateRequest,
    NoteUpdateRequest,
    NoteResponse,
    NoteListResponse,
)
from app.models.user import User
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.repositories.note_repository import NoteRepository
from app.repositories.job_repository import JobRepository
from app.services.note_service import NoteService

router = APIRouter(tags=["Notes"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_service(db: Session) -> NoteService:
    return NoteService(
        repo=NoteRepository(db),
        job_repo=JobRepository(db),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Nested routes:  /jobs/{job_id}/notes
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/jobs/{job_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    job_id: str,
    data: NoteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a note to a specific job application."""
    try:
        return _get_service(db).create_note(
            job_id=job_id,
            user_id=current_user.id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/jobs/{job_id}/notes",
    response_model=NoteListResponse,
)
def list_notes_by_job(
    job_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all notes for a specific job application."""
    try:
        notes, total = _get_service(db).list_by_job(
            job_id=job_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        return NoteListResponse(total=total, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Flat routes:  /notes
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/notes",
    response_model=NoteListResponse,
)
def list_all_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all notes across every job for the authenticated user."""
    notes, total = _get_service(db).list_all(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return NoteListResponse(total=total, notes=notes)


@router.get(
    "/notes/{note_id}",
    response_model=NoteResponse,
)
def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single note by ID."""
    try:
        return _get_service(db).get_note(
            note_id=note_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/notes/{note_id}",
    response_model=NoteResponse,
)
def update_note(
    note_id: str,
    data: NoteUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the content of a note."""
    try:
        return _get_service(db).update_note(
            note_id=note_id,
            user_id=current_user.id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a note."""
    try:
        _get_service(db).delete_note(
            note_id=note_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
