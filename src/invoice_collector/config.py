"""
Configuration management for invoice collector
Loads settings from environment variables
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables
    """

    # Google Sheets Configuration
    SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    RANGE: str = os.getenv("GOOGLE_SHEETS_RANGE", "Invoices!A1:Z999")

    # Gmail Configuration
    GMAIL_SENDER: str = os.getenv("GMAIL_SENDER", "")

    # Application Settings
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Business Hours (24-hour format)
    WINDOW_START: int = int(os.getenv("WINDOW_START", "8"))
    WINDOW_END: int = int(os.getenv("WINDOW_END", "18"))

    # File Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    TEMPLATES_DIR: Path = Path(__file__).parent / "templates"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # OAuth Credentials
    CLIENT_SECRET_FILE: Path = PROJECT_ROOT / "client_secret.json"
    TOKEN_SHEETS_FILE: Path = PROJECT_ROOT / "token_sheets.json"
    TOKEN_GMAIL_FILE: Path = PROJECT_ROOT / "token_gmail.json"

    # Reminder Stages (days overdue)
    STAGES = [7, 14, 21, 28, 35, 42]

    # API Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_API_RETRIES", "4"))
    RETRY_INITIAL_WAIT: int = int(os.getenv("RETRY_INITIAL_WAIT_SECONDS", "1"))

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate required settings are present
        Returns list of validation errors (empty if valid)
        """
        errors = []

        if not cls.SPREADSHEET_ID:
            errors.append("GOOGLE_SHEETS_SPREADSHEET_ID is required")

        if not cls.GMAIL_SENDER:
            errors.append("GMAIL_SENDER is required")

        if not cls.CLIENT_SECRET_FILE.exists():
            errors.append(f"client_secret.json not found at {cls.CLIENT_SECRET_FILE}")

        if not cls.TEMPLATES_DIR.exists():
            errors.append(f"Templates directory not found at {cls.TEMPLATES_DIR}")

        # Ensure logs directory exists
        cls.LOGS_DIR.mkdir(exist_ok=True)

        return errors

    @classmethod
    def is_within_business_hours(cls) -> bool:
        """Check if current time is within configured business hours"""
        from datetime import datetime
        current_hour = datetime.now().hour
        return cls.WINDOW_START <= current_hour < cls.WINDOW_END


# Singleton instance
settings = Settings()
