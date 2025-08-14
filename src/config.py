from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import EmailStr, Field
from typing import List

class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    STORAGE_BACKEND: str = "local"  # Default to local storage
    SUPERADMIN_EMAILS_RAW: str = ""  # Made optional with default
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
    ENVIRONMENT: str = "p"
    DOMAIN: str
    CLIENT_DOMAIN: str = ""  # Made optional with default


    # For S3-compatible storage (S3, R2, MinIO, etc.)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    AWS_BUCKET_NAME: str = ""
    S3_ENDPOINT_URL: str = ""  # For R2/MinIO custom endpoints

    # Cloudflare R2 specific
    R2_ACCOUNT_ID: str = ""  # Your Cloudflare account ID

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""

    @property
    def SUPERADMIN_EMAILS(self) -> List[str]:
        if not self.SUPERADMIN_EMAILS_RAW:
            return []
        return [email.strip() for email in self.SUPERADMIN_EMAILS_RAW.split(",") if email.strip()]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
Config = Settings()


   
