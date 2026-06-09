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

    def register(self, name: str, email: str, password: str) -> tuple[User, str]:
        """
        Create a new user account.
        Returns (user, verification_token) so the router can send the email.
        """
        existing_user = self.repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        verification_token = create_password_reset_token()  # reuse secure random token
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_email_verified=False,
            email_verification_token=verification_token,
            email_verification_expires=expires_at,
        )
        created_user = self.repo.create(user)
        return created_user, verification_token

    # ─── Verify Email ─────────────────────────────────────────────────────────────

    def verify_email(self, token: str) -> tuple[User, str, str]:
        """
        Validate the token, mark email as verified.
        Returns (user, access_token, refresh_token) so the user can be
        auto-logged in after clicking the verification link.
        """
        user = self.repo.get_by_verification_token(token)
        if not user:
            raise ValueError("Invalid or expired verification token")

        expires_at = user.email_verification_expires
        if expires_at is None:
            raise ValueError("Invalid verification token")

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            raise ValueError("Verification token has expired. Please request a new one.")

        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        saved_user = self.repo.save(user)

        # Issue tokens immediately so the app can auto-login on deep link return
        payload = {"sub": str(saved_user.id)}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return saved_user, access_token, refresh_token

    # ─── Resend Verification ──────────────────────────────────────────────────

    def resend_verification(self, email: str) -> tuple[User, str]:
        """
        Generate a fresh verification token for an unverified account.
        Returns (user, new_token) so the router can send the email.
        """
        user = self.repo.get_by_email(email)
        if not user:
            raise ValueError("No account found with this email address")

        if user.is_email_verified:
            raise ValueError("This email address is already verified")

        new_token = create_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )
        user.email_verification_token = new_token
        user.email_verification_expires = expires_at
        self.repo.save(user)
        return user, new_token

    # ─── Login ────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_email_verified:
            raise ValueError(
                "EMAIL_NOT_VERIFIED: Please verify your email before logging in. "
                "Check your inbox or request a new verification email."
            )

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

    def forgot_password(self, email: str) -> tuple[User, str]:
        """
        Generate a password reset token.
        Returns (user, reset_token) so the router can email it.
        Raises ValueError if email not found or email not verified.
        """
        user = self.repo.get_by_email(email)
        if not user:
            raise ValueError("No account found with this email address")

        if not user.is_email_verified:
            raise ValueError(
                "Please verify your email address before resetting your password."
            )

        reset_token = create_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        user.password_reset_token = reset_token
        user.password_reset_expires = expires_at
        self.repo.save(user)
        return user, reset_token

    # ─── Reset Password ───────────────────────────────────────────────────────

    def reset_password(self, token: str, new_password: str) -> None:
        user = self.repo.get_by_reset_token(token)
        if not user:
            raise ValueError("Invalid or expired reset token")

        expires_at = user.password_reset_expires
        if expires_at is None:
            raise ValueError("Invalid or expired reset token")

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
        if not user.is_email_verified:
            raise ValueError("Please verify your email address before changing your password.")

        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        self.repo.save(user)