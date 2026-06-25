from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.models.base_model import BaseModel


class Resume(BaseModel):

    __tablename__ = "resumes"

    # ─── Ownership ────────────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─── Content ──────────────────────────────────────────────────────────────
    original_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    enhanced_text: Mapped[str] = mapped_column(Text, nullable=False)
