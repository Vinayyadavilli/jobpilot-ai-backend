from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from typing import Optional

from app.models.base_model import BaseModel


class User(BaseModel):

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None
    )

    password_reset_expires: Mapped[Optional[DateTime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None
    )