from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
import uuid


# |---- Schemas to Read User data ----|
class UserModel(BaseModel):
    uid: str
    username: str
    first_name: str
    last_name: str
    is_verified: str
    email: str
    password_hash: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        
# |---- Schemas Required to create User ----|
class UserCreateModel(BaseModel):
    email: str
    username: str = Field(max_length=13)
    password: str = Field(min_length=8)
    first_name : str 
    last_name: str
    
# |---- Schemas Required for user to login ----|
class UserLoginModel(BaseModel):
    email: str 
    password: str
    

    
