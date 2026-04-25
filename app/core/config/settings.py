from pydantic_settings import BaseSettings
from pydantic import EmailStr

class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    FRONTEND_URL: str

    # Database settings
    DATABASE_URL: str

    # App settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    EMAIL_TOKEN_EXPIRE_MINUTES: int

    # Email configuration settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    # RBAC Seed Data
    # SEED_ADMIN_EMAIL: EmailStr
    # SEED_ADMIN_PASSWORD: str
    # SEED_ADMIN_FIRST_NAME: str
    # SEED_ADMIN_LAST_NAME: str

    # SEED_USER_EMAIL: EmailStr
    # SEED_USER_PASSWORD: str
    # SEED_USER_FIRST_NAME: str
    # SEED_USER_LAST_NAME: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True


settings = Settings()