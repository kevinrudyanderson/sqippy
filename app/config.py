import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "SQLALCHEMY_DATABASE_URL", "sqlite:///./test.db"
    )

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Environment
    ENV: str = os.getenv("ENV", "development")

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
