from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid


class BookCreateModel(BaseModel):
    title : str
    author : str
    description : str
    upload_date: datetime
    uploadedby: Optional[uuid.UUID]


# A Model to read info from db
class BookReadModel(BaseModel):
    title: str
    author: str
    description: str
    file_size : float
    cover_image : Optional[str]
    upload_date: datetime
    uploaded_by: Optional[uuid.UUID]
    file_url: Optional[str]    