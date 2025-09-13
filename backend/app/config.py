from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "EV AI Diagnostic"
    SECRET_KEYS: List[str] = ["super-secret-key"]  # put primary key first; rotate by adding new keys
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24*7
    DATABASE_URL: str = "sqlite:///./db.sqlite"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    REDIS_URL: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    TWILIO_SID: Optional[str] = None
    TWILIO_AUTH: Optional[str] = None
    TWILIO_FROM: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    MODELS_DIR: str = "./models"
    class Config:
        env_file = '.env'
settings = Settings()