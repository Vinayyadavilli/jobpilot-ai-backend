from sqlalchemy.orm import Session

from app.models.note import Note


class NoteRepository:

    def __init__(self, db: Session):
        self.db = db

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_by_id(self, note_id: str, user_id: str) -> Note | None:
        """Fetch a single note owned by the given user."""
        return (
            self.db.query(Note)
            .filter(Note.id == note_id, Note.user_id == user_id)
            .first()
        )

    def get_by_job(
        self,
        job_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Note], int]:
        """List all notes for a specific job. Returns (items, total_count)."""
        query = (
            self.db.query(Note)
            .filter(Note.job_id == job_id, Note.user_id == user_id)
        )
        total = query.count()
        items = (
            query
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def get_all_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Note], int]:
        """List all notes across all jobs for a user."""
        query = self.db.query(Note).filter(Note.user_id == user_id)
        total = query.count()
        items = (
            query
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    # ─── Write ────────────────────────────────────────────────────────────────

    def create(self, note: Note) -> Note:
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def save(self, note: Note) -> Note:
        self.db.commit()
        self.db.refresh(note)
        return note

    def delete(self, note: Note) -> None:
        self.db.delete(note)
        self.db.commit()
