import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Project settings
    PROJECT_NAME: str = "Log Reporter"
    API_STR: str = "/api"

    # CORS settings
    ALL_CORS_ORIGINS: List[str] = [
        os.getenv("FRONTEND_URL"),  # Default value
        os.getenv("BACKEND_URL" ),  # Default value
        os.getenv("MONGODB_URL" )  # Default value
    ]

    # Upload directory
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    #Filename
    FILENAME_REGEX: str = r"transactions_(\d{8})\.zip"

    # Sentry settings
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")

    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "logs")
    MONGODB_LOGIN: str = os.getenv("MONGODB_LOGIN")
    MONGODB_COLLECTION_NAME: str = os.getenv("MONGODB_MASTER_COLLECTION_NAME", "Master")
    MONGODB_DAILY_SUMM_COLLECTION_NAME: str = os.getenv("MONGODB_DAILY_SUMMARY_COLLECTION_NAME","Daily_Transaction_Summary")
    MONGODB_SUMM_COLLECTION_NAME: str = os.getenv("MONGODB_SUMMARY_COLLECTION_NAME","Transaction_summary")
    MONGODB_TOKENS_COLLECTION_NAME: str = os.getenv("MONGODB_TOKENS_COLLECTION_NAME", "Token_Registry")
    MONGODB_TEMP_TOKENS_COLLECTION_NAME: str = os.getenv("MONGODB_TEMP_TOKENS_COLLECTION_NAME", "tempTokens")
    MONGODB_TEMP_COLLECTION_NAME: str = os.getenv("MONGODB_TEMP_COLLECTION_NAME","Temp")
    MONGODB_REFRESH_TOKEN_NAME:str=os.getenv("MONGODB_REFRESH_TOKEN_NAME","Refresh_Token")

    #JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY","VerySecret")
    ALGORITHM: str = os.getenv("ALGORITHM","")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",60))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS",7))

    class Config:
        env_file = ".env"

settings = Settings()