from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import EmailStr, Field
from typing import List

class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_BACKEND: str
    SUPERADMIN_EMAILS_RAW: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

     # --- App Config ---
    ENVIRONMENT: str = "development"
    DOMAIN: str
    CLIENT_DOMAIN: str

    
    # For Future s3 bucket
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    
    @property
    def SUPERADMIN_EMAILS(self) -> List[str]:
        return [email.strip() for email in self.SUPERADMIN_EMAILS_RAW.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
Config = Settings()


   
