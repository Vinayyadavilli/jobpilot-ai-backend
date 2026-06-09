from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Note(BaseModel):

    __tablename__ = "notes"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    job: Mapped["Job"] = relationship("Job", back_populates="notes")  # noqa: F821
