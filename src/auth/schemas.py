from pydantic import BaseModel, Field, ConfigDict
from src.books.schemas import BookInDownloadLog # This import is now correct
from datetime import datetime
from typing import List, Optional
import uuid

# This is the public-facing schema for a user. It safely exposes only non-sensitive data.
class UserPublicModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: uuid.UUID
    first_name: str
    last_name: str
    is_verified: bool
    email: str
    role: str
    created_at: datetime

# |---- Schemas Required to create User ----|
class UserCreateModel(BaseModel):
    email: str
    # username: str = Field(max_length=13) |--- Reserved for Future Use ---|
    password: str = Field(min_length=8)
    first_name : str 
    last_name: str
    
# |---- Schemas Required for user to login ----|
class UserLoginModel(BaseModel):
    email: str 
    password: str
    
# |--- Schemas for User to update Profile Info ---|
class UserUpdateModel(BaseModel):
    first_name : Optional[str] = None
    last_name: Optional[str] = None
    
class ForgotPasswordSchema(BaseModel):
    email:str
    
class PasswordChangeSchema(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, description="New password must be at least 8 characters long")
    
class ResetPasswordSchema(BaseModel):
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    confirm_password: str = Field(min_length=8, description="Confirm password must be at least 8 characters long")
    
class UserDownloadHistoryModel(BaseModel):
    timestamp: datetime
    book: BookInDownloadLog

    model_config = ConfigDict(from_attributes=True)


class LogoutSchema(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")