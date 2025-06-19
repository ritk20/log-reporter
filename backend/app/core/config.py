import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Project settings
    PROJECT_NAME: str = "Log Reporter"
    API_STR: str = "/api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 
    REFRESH_TOKEN_EXPIRE_DAYS :int = 30
    

    # CORS settings
    ALL_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
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
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "logs2")
    MONGODB_COLLECTION_NAME: str = os.getenv("MONGODB_COLLECTION_NAME", "master2")
    MONGODB_DAILY_SUMM_COLLECTION_NAME: str = os.getenv("MONGODB_DAILY_SUMM_COLLECTION_NAME","Daily_Transaction_Summary2")
    MONGODB_SUMM_COLLECTION_NAME: str = os.getenv("MONGODB_SUMM_COLLECTION_NAME","Transaction_summary2")
    MONGODB_TOKENS_COLLECTION_NAME: str = os.getenv("MONGODB_TOKENS_COLLECTION_NAME", "tokens")
    MONGODB_TEMP_TOKENS_COLLECTION_NAME: str = os.getenv("MONGODB_TEMP_TOKENS_COLLECTION_NAME", "tempTokens2")
    MONGODB_TEMP_COLLECTION_NAME: str = os.getenv("MONGODB_TEMP_COLLECTION_NAME","Temp2")
    MONGODB_REFRESH_TOKEN_NAME:str=os.getenv("MONGODB_REFRESH_TOKEN_NAME","Refresh_Token")
    MONGODB_LOGIN:str=os.getenv("MONGODB_LOGIN","login_collection")


    class Config:
        env_file = ".env"

settings = Settings()