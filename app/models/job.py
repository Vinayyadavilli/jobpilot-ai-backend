import enum

from sqlalchemy import String, Text, Date, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base_model import BaseModel


class JobStatus(str, enum.Enum):
    applied      = "applied"
    interviewing = "interviewing"
    offered      = "offered"
    rejected     = "rejected"
    withdrawn    = "withdrawn"


class Job(BaseModel):

    __tablename__ = "jobs"

    # ─── Ownership ────────────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─── Core Fields ──────────────────────────────────────────────────────────
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.applied
    )

    # ─── Optional Details ─────────────────────────────────────────────────────
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    applied_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    job_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    interviews: Mapped[list] = relationship(
        "Interview", back_populates="job", cascade="all, delete-orphan"
    )
    notes: Mapped[list] = relationship(
        "Note", back_populates="job", cascade="all, delete-orphan"
    )
