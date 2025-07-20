from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid


class BookCreateModel(BaseModel):
    title : str
    author : str
    description : str
    upload_date: datetime
    uploaded_by: Optional[uuid.UUID]
    
class BookUpdateModel(BaseModel):
    title: Optional[str]
    author: Optional[str]
    description: Optional[str]

# a response model for book search
class BookSearchModel(BaseModel):
    uid: uuid.UUID
    title: str
    author: str
    description: str
    cover_image: Optional[str]
    upload_date: datetime
    
    class Config:
        from_attributes = True