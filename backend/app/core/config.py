import os
from typing import List

class Settings:
    # Project settings
    PROJECT_NAME: str = "Log Reporter"
    API_STR: str = "/api"

    # CORS settings
    ALL_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
    ]

    # Upload directory
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    #Filename
    FILENAME_REGEX: str = r"transactions_(\d{8})\.zip"

    # Sentry settings
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")

settings = Settings()