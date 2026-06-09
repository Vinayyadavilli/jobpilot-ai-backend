from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    ResendVerificationRequest,
)
from app.schemas.user import UserResponse
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.config import settings
from app.core.email import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_service(db: Session) -> AuthService:
    return AuthService(UserRepository(db))


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new account.
    A verification email is sent immediately — the user must verify before logging in.
    """
    try:
        user, verification_token = _get_service(db).register(
            name=request.name,
            email=request.email,
            password=request.password,
        )
        # Send verification email in background (non-blocking)
        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            name=user.name,
            token=verification_token,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── Verify Email ─────────────────────────────────────────────────────────────

def _verification_success_html(name: str, deep_link: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Email Verified — JobPilot AI</title>
      <meta http-equiv="refresh" content="3;url={deep_link}"/>
      <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', Arial, sans-serif;
          background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
          min-height: 100vh; display: flex; align-items: center; justify-content: center;
        }}
        .card {{
          background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 24px; padding: 48px 40px; max-width: 420px; width: 90%;
          text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.4);
        }}
        .icon {{ font-size: 64px; margin-bottom: 24px; animation: pop 0.5s ease; }}
        @keyframes pop {{
          0% {{ transform: scale(0); opacity: 0; }}
          70% {{ transform: scale(1.2); }}
          100% {{ transform: scale(1); opacity: 1; }}
        }}
        h1 {{ color: #ffffff; font-size: 28px; font-weight: 700; margin-bottom: 12px; }}
        p {{ color: rgba(255,255,255,0.65); font-size: 16px; line-height: 1.6; margin-bottom: 32px; }}
        .open-btn {{
          display: inline-block; background: linear-gradient(135deg, #2563EB, #7C3AED);
          color: white; padding: 16px 40px; border-radius: 50px;
          text-decoration: none; font-weight: 600; font-size: 17px;
          box-shadow: 0 8px 25px rgba(37,99,235,0.4);
          transition: transform 0.2s, box-shadow 0.2s;
        }}
        .open-btn:hover {{ transform: translateY(-2px); box-shadow: 0 12px 30px rgba(37,99,235,0.5); }}
        .redirect-note {{
          margin-top: 20px; color: rgba(255,255,255,0.35); font-size: 13px;
        }}
        .progress {{
          width: 100%; height: 3px; background: rgba(255,255,255,0.1);
          border-radius: 3px; margin-top: 24px; overflow: hidden;
        }}
        .progress-bar {{
          height: 100%; background: linear-gradient(90deg, #2563EB, #7C3AED);
          animation: fill 3s linear forwards;
        }}
        @keyframes fill {{ from {{ width: 0%; }} to {{ width: 100%; }} }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="icon">✅</div>
        <h1>Email Verified!</h1>
        <p>Hey <strong style="color:#fff">{name}</strong>, your JobPilot AI account is now active and ready to use.</p>
        <a href="{deep_link}" class="open-btn">Open JobPilot App</a>
        <p class="redirect-note">Redirecting to the app automatically...</p>
        <div class="progress"><div class="progress-bar"></div></div>
      </div>
      <script>
        // Auto-redirect after 3 seconds using the deep link
        setTimeout(() => {{ window.location.href = "{deep_link}"; }}, 3000);
      </script>
    </body>
    </html>
    """


def _verification_error_html(error_message: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Verification Failed — JobPilot AI</title>
      <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', Arial, sans-serif;
          background: linear-gradient(135deg, #0f172a 0%, #3b1a1a 100%);
          min-height: 100vh; display: flex; align-items: center; justify-content: center;
        }}
        .card {{
          background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
          border: 1px solid rgba(255,100,100,0.2);
          border-radius: 24px; padding: 48px 40px; max-width: 420px; width: 90%;
          text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.4);
        }}
        .icon {{ font-size: 64px; margin-bottom: 24px; }}
        h1 {{ color: #ffffff; font-size: 28px; font-weight: 700; margin-bottom: 12px; }}
        p {{ color: rgba(255,255,255,0.65); font-size: 16px; line-height: 1.6; }}
        .err {{ color: #FCA5A5; font-size: 14px; margin-top: 16px;
               background: rgba(220,38,38,0.15); padding: 12px 16px; border-radius: 10px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="icon">❌</div>
        <h1>Verification Failed</h1>
        <p>Something went wrong with your verification link.</p>
        <p class="err">{error_message}</p>
        <p style="margin-top:24px; color:rgba(255,255,255,0.4); font-size:13px;">
          Open the JobPilot app and tap <strong style="color:white">Resend Verification Email</strong> to get a new link.
        </p>
      </div>
    </body>
    </html>
    """


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(
    token: str = Query(..., description="Verification token from the email link"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    Called when the user clicks the verification link in their email.
    - Verifies the token
    - Issues JWT tokens immediately
    - Returns an HTML page with a deep link button that opens the iOS app
      and passes the tokens → user is auto-logged in on the app side
    """
    try:
        user, access_token, refresh_token = _get_service(db).verify_email(token)

        # Send welcome email in background
        background_tasks.add_task(
            send_welcome_email,
            email=user.email,
            name=user.name,
        )

        # Build deep link — iOS app catches this URL scheme
        # jobpilot://auth/verified?access_token=xxx&refresh_token=xxx
        deep_link = (
            f"{settings.APP_DEEP_LINK_SCHEME}://auth/verified"
            f"?access_token={access_token}"
            f"&refresh_token={refresh_token}"
        )

        return HTMLResponse(
            content=_verification_success_html(user.name, deep_link),
            status_code=200,
        )

    except ValueError as e:
        return HTMLResponse(
            content=_verification_error_html(str(e)),
            status_code=400,
        )



# ─── Resend Verification Email ────────────────────────────────────────────────

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Resend a verification email for accounts that haven't verified yet.
    Generates a fresh token with a new 60-minute expiry.
    """
    try:
        user, new_token = _get_service(db).resend_verification(email=request.email)
        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            name=user.name,
            token=new_token,
        )
        return {"message": "Verification email sent. Please check your inbox."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate and receive access + refresh tokens.
    Returns 403 if email is not verified yet.
    """
    try:
        tokens = _get_service(db).login(
            email=request.email,
            password=request.password,
        )
        return TokenResponse(**tokens)
    except ValueError as e:
        error_msg = str(e)
        # Distinguish unverified email from bad credentials
        if "EMAIL_NOT_VERIFIED" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "EMAIL_NOT_VERIFIED",
                    "message": "Please verify your email address before logging in.",
                    "hint": "Use POST /api/v1/auth/resend-verification to get a new link.",
                },
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg)


# ─── Refresh Token ────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        tokens = _get_service(db).refresh_access_token(request.refresh_token)
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ─── Get Current User (Me) ────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


# ─── Forgot Password ──────────────────────────────────────────────────────────

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Request a password reset.
    Sends the reset token via email. Only works for verified accounts.
    """
    try:
        user, reset_token = _get_service(db).forgot_password(email=request.email)
        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            name=user.name,
            reset_token=reset_token,
        )
        return {"message": "Password reset instructions have been sent to your email."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── Reset Password ───────────────────────────────────────────────────────────

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using the token received via email."""
    try:
        _get_service(db).reset_password(
            token=request.token,
            new_password=request.new_password,
        )
        return {"message": "Password has been reset successfully. You can now log in."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── Change Password ──────────────────────────────────────────────────────────

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password for the currently authenticated user. Requires a verified email."""
    try:
        _get_service(db).change_password(
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return {"message": "Password changed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint.
    JWTs are stateless — the client must discard both tokens on logout.
    """
    return {"message": "Logged out successfully. Please discard your tokens."}