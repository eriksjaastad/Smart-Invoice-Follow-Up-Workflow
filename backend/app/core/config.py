"""Application configuration using Pydantic Settings"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# Project root is three levels up from this file (config.py -> core -> app -> backend -> root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Single .env file lives at project root (not backend/).
    """

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    system_paused: bool = False  # Global kill switch (FR-21)
    
    # Database
    database_url: str
    
    # Auth0
    auth0_domain: str = ""
    auth0_client_id: str = ""
    auth0_client_secret: str = ""
    auth0_audience: str = ""
    auth0_callback_url: str = ""
    jwt_secret: str = ""
    secret_key: str = "your-secret-key-change-in-production"  # Added for SessionMiddleware

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # Make.com
    make_webhook_api_key: str = ""
    make_api_url: str = "https://hook.integromat.com"
    make_list_sheets_webhook_url: str = ""
    make_validate_sheet_webhook_url: str = ""
    make_create_template_webhook_url: str = ""

    # Resend
    resend_api_key: str = ""
    resend_from_email: str = "noreply@send.synthinsightlabs.com"

    # Digest Cron
    digest_cron_secret: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

