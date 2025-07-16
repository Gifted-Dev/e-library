from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import ForeignKey, String
from datetime import datetime
from typing import List, Optional
# from src.db.main import Base
import sqlalchemy.dialects.postgresql as pg
import uuid 

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
            default=uuid.uuid4
        )
    )
    
    username: Optional[str] = Field(default=None)
    first_name: str = Field(nullable=True)
    last_name: str = Field(nullable=True)
    
    role: str = Field(
        sa_column=Column(
            pg.VARCHAR, 
            nullable=False, 
            server_default="user")
    )
    
    is_verified: bool = False
    email: str
    password_hash: str
    created_at: datetime = Field(sa_column=Column(
        pg.TIMESTAMP,
        default=datetime.now
    ))
    
    
class Book(SQLModel, table=True):
    __tablename__ = "books"
    
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
            default=uuid.uuid4
        )
    )
    
    title: str = Field(nullable=False)
    author: str = Field(nullable=False)
    description: str = Field(nullable=False)
    file_url: str  = Field(nullable=False)
    file_size: float  = Field(nullable=False)
    cover_image: Optional[str] = None
    uploaded_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    upload_date: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            default=datetime.now,
        )
    )
    
    


# creating downloads table to track user downloads
class Downloads(SQLModel, table=True):
    __tablename__ = "downloads"
    
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
            default=uuid.uuid4
        )
    )
    
    user_id: Optional[uuid.UUID] = Field(
        sa_column=Column(
            ForeignKey("users.uid"),
            default=None,
            nullable=True
        )
    )
    
    book_id: Optional[uuid.UUID] = Field(
        sa_column=Column(
            ForeignKey("books.uid"),
            default=None,
            nullable=True
        )
    )
    
    timestamp: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            default=datetime.now
        )
    )
    
    was_emailed: Optional[bool] = Field(
        sa_column=Column(
            pg.BOOLEAN,
            nullable=False,
            server_default="false"
        )
    )