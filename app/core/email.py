from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings


# ─── Mail Connection Config ───────────────────────────────────────────────────

def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


# ─── HTML Templates ───────────────────────────────────────────────────────────

def _verification_email_html(name: str, verification_link: str) -> str:
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
        <div style="max-width: 520px; margin: auto; background: white; border-radius: 10px;
                    padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
          <h2 style="color: #2563EB; margin-bottom: 8px;">Welcome to JobPilot AI 👋</h2>
          <p style="color: #374151;">Hi <strong>{name}</strong>,</p>
          <p style="color: #374151;">
            Thanks for signing up! Please verify your email address to activate your account.
            This link expires in <strong>60 minutes</strong>.
          </p>
          <div style="text-align: center; margin: 32px 0;">
            <a href="{verification_link}"
               style="background: #2563EB; color: white; padding: 14px 32px;
                      border-radius: 8px; text-decoration: none; font-weight: bold;
                      font-size: 16px;">
              Verify Email Address
            </a>
          </div>
          <p style="color: #6B7280; font-size: 13px;">
            Or copy and paste this link into your browser:<br/>
            <a href="{verification_link}" style="color: #2563EB;">{verification_link}</a>
          </p>
          <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;"/>
          <p style="color: #9CA3AF; font-size: 12px;">
            If you didn't create an account, you can safely ignore this email.
          </p>
        </div>
      </body>
    </html>
    """


def _password_reset_email_html(name: str, reset_token: str) -> str:
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
        <div style="max-width: 520px; margin: auto; background: white; border-radius: 10px;
                    padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
          <h2 style="color: #DC2626; margin-bottom: 8px;">Password Reset Request 🔐</h2>
          <p style="color: #374151;">Hi <strong>{name}</strong>,</p>
          <p style="color: #374151;">
            We received a request to reset your password.
            Use the token below in the reset password form. It expires in <strong>15 minutes</strong>.
          </p>
          <div style="text-align: center; margin: 32px 0;">
            <div style="background: #F3F4F6; border-radius: 8px; padding: 16px 24px;
                        font-family: monospace; font-size: 18px; letter-spacing: 2px;
                        color: #111827; word-break: break-all;">
              {reset_token}
            </div>
          </div>
          <p style="color: #374151; font-size: 14px;">
            Use this token at <code>POST /api/v1/auth/reset-password</code> with your new password.
          </p>
          <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;"/>
          <p style="color: #9CA3AF; font-size: 12px;">
            If you didn't request a password reset, please ignore this email.
            Your password will not change.
          </p>
        </div>
      </body>
    </html>
    """


def _welcome_email_html(name: str) -> str:
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
        <div style="max-width: 520px; margin: auto; background: white; border-radius: 10px;
                    padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
          <h2 style="color: #059669; margin-bottom: 8px;">Email Verified! 🎉</h2>
          <p style="color: #374151;">Hi <strong>{name}</strong>,</p>
          <p style="color: #374151;">
            Your email has been successfully verified. Your JobPilot AI account is now fully active.
          </p>
          <p style="color: #374151;">
            Start tracking your job applications, schedule interviews, and take notes — all in one place.
          </p>
          <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;"/>
          <p style="color: #9CA3AF; font-size: 12px;">
            Welcome aboard — the JobPilot AI Team 🚀
          </p>
        </div>
      </body>
    </html>
    """


# ─── Send Functions ───────────────────────────────────────────────────────────

async def send_verification_email(email: str, name: str, token: str) -> None:
    """Send email verification link to newly registered user."""
    verification_link = (
        f"{settings.APP_BASE_URL}/api/v1/auth/verify-email?token={token}"
    )
    message = MessageSchema(
        subject="Verify your JobPilot AI account",
        recipients=[email],
        body=_verification_email_html(name, verification_link),
        subtype=MessageType.html,
    )
    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


async def send_password_reset_email(email: str, name: str, reset_token: str) -> None:
    """Send password reset token to the user's email."""
    message = MessageSchema(
        subject="Reset your JobPilot AI password",
        recipients=[email],
        body=_password_reset_email_html(name, reset_token),
        subtype=MessageType.html,
    )
    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


async def send_welcome_email(email: str, name: str) -> None:
    """Send a welcome email once the user has verified their account."""
    message = MessageSchema(
        subject="Welcome to JobPilot AI 🚀",
        recipients=[email],
        body=_welcome_email_html(name),
        subtype=MessageType.html,
    )
    fm = FastMail(_get_mail_config())
    await fm.send_message(message)
