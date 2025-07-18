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
        os.getenv("BACKEND_URL"),
        os.getenv("FRONTEND_URL"),
        os.getenv("MONGODB_URL" ) 
        
    ]

    # Upload directory
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    #Filename
    FILENAME_REGEX: str = r"transactions_(\d{8})\.zip"

    # Sentry settings
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")

    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "url")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "logs2")
    MONGODB_LOGIN: str = os.getenv("MONGODB_LOGIN", "Users2")
    MONGODB_COLLECTION_NAME: str = os.getenv("MONGODB_COLLECTION_NAME", "master2")
    MONGODB_DAILY_SUMM_COLLECTION_NAME: str = os.getenv("MONGODB_DAILY_SUMM_COLLECTION_NAME","Daily_Transaction_Summary2")
    MONGODB_SUMM_COLLECTION_NAME: str = os.getenv("MONGODB_SUMM_COLLECTION_NAME","Transaction_summary2")
    MONGODB_TOKENS_COLLECTION_NAME: str = os.getenv("MONGODB_TOKENS_COLLECTION_NAME", "tokens")
    MONGODB_TEMP_TOKENS_COLLECTION_NAME: str = os.getenv("MONGODB_TEMP_TOKENS_COLLECTION_NAME", "tempTokens2")
    MONGODB_TEMP_COLLECTION_NAME: str = os.getenv("MONGODB_TEMP_COLLECTION_NAME","Temp2")
    MONGODB_REFRESH_TOKEN_NAME:str=os.getenv("MONGODB_REFRESH_TOKEN_NAME","Refresh_Token")

    #JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY","VerySecret")
    ALGORITHM: str = os.getenv("ALGORITHM","")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",60))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS",7))

    class Config:
        env_file = ".env"

settings = Settings()
