import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _get_bool(env_var_name: str, default: bool = False) -> bool:
    """Read a boolean environment variable with a sensible default."""
    value = os.getenv(env_var_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


class Settings:
    # Environment
    ENV: str = os.getenv("ENV", "development")

    # Database
    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "SQLALCHEMY_DATABASE_URL", "sqlite:///./test.db"
    )

    # PostgreSQL specific settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sqipit")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "sqipit_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL URL from individual components"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Cookies
    REFRESH_TOKEN_COOKIE_NAME: str = os.getenv(
        "REFRESH_TOKEN_COOKIE_NAME", "refresh_token"
    )
    COOKIE_DOMAIN: Optional[str] = os.getenv("COOKIE_DOMAIN")
    COOKIE_PATH: str = os.getenv("COOKIE_PATH", "/")
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax").strip().lower()
    COOKIE_SECURE: bool = _get_bool(
        "COOKIE_SECURE", default=ENV.strip().lower() == "production"
    )

    # Subscription Tiers
    FREE_QUEUE_LIMIT: int = int(os.getenv("FREE_QUEUE_LIMIT", "1"))
    PRO_QUEUE_LIMIT: int = int(os.getenv("PRO_QUEUE_LIMIT", "5"))
    BUSINESS_QUEUE_LIMIT: int = int(os.getenv("BUSINESS_QUEUE_LIMIT", "999"))

    FREE_SMS_CREDITS: int = int(os.getenv("FREE_SMS_CREDITS", "0"))
    PRO_SMS_CREDITS: int = int(os.getenv("PRO_SMS_CREDITS", "100"))
    BUSINESS_SMS_CREDITS: int = int(os.getenv("BUSINESS_SMS_CREDITS", "500"))

    FREE_DEACTIVATION_DAYS: int = int(os.getenv("FREE_DEACTIVATION_DAYS", "30"))
    PRO_DEACTIVATION_DAYS: int = int(os.getenv("PRO_DEACTIVATION_DAYS", "90"))

    # Stripe (when ready)
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # SMS Providers (Twilio preferred, Prelude fallback)
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    PRELUDE_API_TOKEN: Optional[str] = os.getenv("PRELUDE_API_TOKEN")

    # Email Provider
    POSTMARK_SERVER_TOKEN: Optional[str] = os.getenv("POSTMARK_SERVER_TOKEN")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@sqipit.com")


settings = Settings()
