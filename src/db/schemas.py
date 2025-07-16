from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class BookCreate(BaseModel):
    title : str
    author : str