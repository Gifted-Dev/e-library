from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import ForeignKey, String
from datetime import datetime
from typing import List, Optional
# from src.db.main import Base
import sqlalchemy.dialects.sqlite as sq
import uuid 

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    uid: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        sa_column=Column(
            String(32),
            primary_key=True,
            # default=lambda: uuid.uuid4().hex
        )
    )
    
    username: str
    firstname: str = Field(nullable=True)
    Lastname: str = Field(nullable=True)
    
    role: str = Field(
        sa_column=Column(
            sq.VARCHAR, 
            nullable=False, 
            server_default="user")
    )
    
    is_verified: bool = False
    email: str
    password_hash: str
    created_at: datetime = Field(sa_column=Column(
        sq.TIMESTAMP,
        default=datetime.now
    ))
    
    books: Optional["Book"] = Relationship(
        back_populates="users"
    )
    
class Book(SQLModel, table=True):
    __tablename__ = "books"
    
    uid: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        sa_column=Column(
            String(32),
            primary_key=True,
            # default=lambda: uuid.uuid4().hex
        )
    )
    
    title: str
    author: str
    file_url: str
    file_size: float
    cover_image: Optional[str] = None
    upload_date: datetime = Field(
        sa_column=Column(
            sq.TIMESTAMP,
            default=datetime.now
        )
    )
    
    users: Optional["Book"] = Relationship(
        back_populates="books",
        sa_relationship_kwargs={"lazy": "selectin"}
    )