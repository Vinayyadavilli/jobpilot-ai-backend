from app.models.note import Note
from app.repositories.note_repository import NoteRepository
from app.repositories.job_repository import JobRepository
from app.schemas.note import NoteCreateRequest, NoteUpdateRequest


class NoteService:

    def __init__(self, repo: NoteRepository, job_repo: JobRepository):
        self.repo = repo
        self.job_repo = job_repo

    # ─── Create ───────────────────────────────────────────────────────────────

    def create_note(
        self,
        job_id: str,
        user_id: str,
        data: NoteCreateRequest,
    ) -> Note:
        # Verify the job exists and belongs to this user
        job = self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise ValueError("Job not found")

        note = Note(
            job_id=job_id,
            user_id=user_id,
            content=data.content,
        )
        return self.repo.create(note)

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_note(self, note_id: str, user_id: str) -> Note:
        note = self.repo.get_by_id(note_id, user_id)
        if not note:
            raise ValueError("Note not found")
        return note

    def list_by_job(
        self,
        job_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Note], int]:
        # Verify job ownership before listing
        job = self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise ValueError("Job not found")

        return self.repo.get_by_job(
            job_id=job_id,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    def list_all(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Note], int]:
        return self.repo.get_all_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    # ─── Update ───────────────────────────────────────────────────────────────

    def update_note(
        self,
        note_id: str,
        user_id: str,
        data: NoteUpdateRequest,
    ) -> Note:
        note = self.get_note(note_id, user_id)
        note.content = data.content
        return self.repo.save(note)

    # ─── Delete ───────────────────────────────────────────────────────────────

    def delete_note(self, note_id: str, user_id: str) -> None:
        note = self.get_note(note_id, user_id)
        self.repo.delete(note)
