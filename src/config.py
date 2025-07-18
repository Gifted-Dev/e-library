from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import EmailStr, Field
from typing import List

class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    STORAGE_BACKEND: str
    SUPERADMIN_EMAILS_RAW: str
    
    @property
    def SUPERADMIN_EMAILS(self) -> List[str]:
        return [email.strip() for email in self.SUPERADMIN_EMAILS_RAW.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
Config = Settings()