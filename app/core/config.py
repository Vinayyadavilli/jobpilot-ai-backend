from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str

    MYSQL_HOST: str
    MYSQL_PORT: int

    MYSQL_USER: str
    MYSQL_PASSWORD: str

    MYSQL_DB: str

    DEBUG: bool = False

    # ─── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60

    # ─── Email / SMTP ─────────────────────────────────────────────────────────
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "JobPilot AI"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # ─── App URL (used in email links) ────────────────────────────────────────
    APP_BASE_URL: str = "http://localhost:8000"

    # ─── iOS Deep Link Scheme ─────────────────────────────────────────────────
    # Must match the URL scheme registered in your iOS app's Info.plist
    APP_DEEP_LINK_SCHEME: str = "jobpilot"

    class Config:
        env_file = ".env"


settings = Settings()