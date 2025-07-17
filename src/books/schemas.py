from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BookCreateModel(BaseModel):
    title : str
    author : str
    description : str


# A Model to read info from db
class BookReadModel(BaseModel):
    title: str
    author: str
    description: str
    file_size : float
    cover_image : Optional[str]
    upload_date: datetime
    uploaded_by: Optional[str]
    file_url: Optional[str]    