from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str

    MYSQL_HOST: str
    MYSQL_PORT: int

    MYSQL_USER: str
    MYSQL_PASSWORD: str

    MYSQL_DB: str

    DEBUG: bool = False

    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    class Config:
        env_file = ".env"


settings = Settings()