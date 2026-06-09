from sqlalchemy import String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum

from app.models.base_model import BaseModel


class InterviewType(str, enum.Enum):
    phone      = "phone"
    video      = "video"
    onsite     = "onsite"
    assignment = "assignment"


class InterviewStatus(str, enum.Enum):
    scheduled   = "scheduled"
    completed   = "completed"
    cancelled   = "cancelled"
    rescheduled = "rescheduled"


class Interview(BaseModel):

    __tablename__ = "interviews"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    round: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType), nullable=False, default=InterviewType.video
    )

    scheduled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus), nullable=False, default=InterviewStatus.scheduled
    )

    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interviewer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    job: Mapped["Job"] = relationship("Job", back_populates="interviews")  # noqa: F821
