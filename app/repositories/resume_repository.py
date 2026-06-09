from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.resume import Resume


class ResumeRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, resume: Resume) -> Resume:
        """Create a new resume enhancement log."""
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_id(self, resume_id: str, user_id: str) -> Optional[Resume]:
        """Retrieve a specific resume enhancement log."""
        return (
            self.db.query(Resume)
            .filter(Resume.id == resume_id, Resume.user_id == user_id)
            .first()
        )

    def get_all_for_user(self, user_id: str) -> List[Resume]:
        """Retrieve all resume enhancement logs for a user, sorted by date desc."""
        return (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc(), Resume.id.desc())
            .all()
        )
