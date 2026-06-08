from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_token,
)
from app.core.config import settings
import jwt


class AuthService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    # ─── Register ─────────────────────────────────────────────────────────────

    def register(self, name: str, email: str, password: str) -> User:
        existing_user = self.repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
        )
        return self.repo.create(user)

    # ─── Login ────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        payload = {"sub": str(user.id)}
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "token_type": "bearer",
        }

    # ─── Refresh Token ────────────────────────────────────────────────────────

    def refresh_access_token(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired, please log in again")
        except jwt.PyJWTError:
            raise ValueError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        new_payload = {"sub": str(user.id)}
        return {
            "access_token": create_access_token(new_payload),
            "refresh_token": create_refresh_token(new_payload),
            "token_type": "bearer",
        }

    # ─── Forgot Password ──────────────────────────────────────────────────────

    def forgot_password(self, email: str) -> str:
        """
        Generates and stores a password-reset token for the user.
        Returns the reset token (caller should email it to the user).
        Raises ValueError if the email is not registered.
        """
        user = self.repo.get_by_email(email)
        if not user:
            raise ValueError("No account found with this email address")

        reset_token = create_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        user.password_reset_token = reset_token
        user.password_reset_expires = expires_at
        self.repo.save(user)

        return reset_token

    # ─── Reset Password ───────────────────────────────────────────────────────

    def reset_password(self, token: str, new_password: str) -> None:
        user = self.repo.get_by_reset_token(token)
        if not user:
            raise ValueError("Invalid or expired reset token")

        # Check expiry
        expires_at = user.password_reset_expires
        if expires_at is None:
            raise ValueError("Invalid or expired reset token")

        # Make expires_at timezone-aware for comparison
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            raise ValueError("Reset token has expired")

        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        self.repo.save(user)

    # ─── Change Password ──────────────────────────────────────────────────────

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        self.repo.save(user)