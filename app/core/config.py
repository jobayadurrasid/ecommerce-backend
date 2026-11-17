from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "E-commerce Ordering & Payment System"
    DEBUG: bool = True
    SECRET_KEY: str = "super-secret-key"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ecommerce"
    REDIS_URL: str = "redis://localhost:6379/0"

    ALLOWED_ORIGINS: list[str] = ["*"]

    # JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Stripe Settings
    STRIPE_SECRET_KEY: Optional[str] = ""
    STRIPE_WEBHOOK_SECRET: Optional[str] = ""

    # bKash Settings
    BKASH_APP_KEY: Optional[str] = ""
    BKASH_APP_SECRET: Optional[str] = ""
    BKASH_USERNAME: Optional[str] = ""
    BKASH_PASSWORD: Optional[str] = ""
    BKASH_BASE_URL: Optional[str] = "https://tokenized.sandbox.bka.sh/v2.0-beta"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
