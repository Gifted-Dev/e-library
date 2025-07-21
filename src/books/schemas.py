from pydantic import BaseModel, ConfigDict
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
    # Add a default value of None to make these fields truly optional in the request body.
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None

# a response model for book search
class BookSearchModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uid: uuid.UUID
    title: str
    author: str
    description: str
    cover_image: Optional[str]
    upload_date: datetime
    