from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.schemas import BookCreateModel
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlmodel import select, desc
from src.db.models import Book
from datetime import datetime
from typing import Optional
from uuid import UUID

class BookService:
    async def save_book(self, book_data: BookCreateModel,
                        file_url: str,
                        file_size: float,
                        uploaded_by: UUID,
                        session:AsyncSession):
        
        # |--- statement to confirm if book has been previously uploaded ---|
        statement = select(Book).where(Book.title == book_data.title,
                                         Book.author == book_data.author)
        
        result = await session.exec(statement) # Execute the statement
        book_exists = result.first() # Result if book exist or not
        
        # |--- If book exist raise exception error ---|
        if book_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book already exists"
            )
        
        # |--- If book does not exist, save book ---|
        new_book_dict = book_data.model_dump()
        new_book = Book(**new_book_dict)
        
        new_book.upload_date = datetime.now()
        new_book.uploaded_by = uploaded_by
        new_book.file_size = file_size
        new_book.file_url = file_url
        
        session.add(new_book)
        await session.commit()
        
        return new_book
        
    
    async def get_all_books(self, session:AsyncSession):
        # |--- Run statement to get all books ---|
        statement = select(Book).order_by(desc(Book.upload_date))
        
        # |--- Excecute the statement and save in variable result ---|
        result = await session.exec(statement)
        
        # show all the results
        return result.all()
    
    async def get_book(self, book_uid:str, session:AsyncSession):
        # To get a book by its UID
        uid_update = UUID(book_uid)
        
        # |--- Run statement to check if book exists ---|
        statement = select(Book).where(Book.uid == uid_update)
        
        # |--- Execute Statement and save in variable "result"---|
        result = await session.exec(statement)
    
        book = result.first()
        
        # |--- Throw Exception if no book is found ---|
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book is not available"
            )
        
        
        return book
    
    async def search_book(self, title: Optional[str], author: Optional[str], session:AsyncSession):
        # |--- Statement to check which the user search for ---|
        statement = select(Book)
        
        if title: # if user searches with the title
            statement = statement.where(Book.title.ilike(f"%{title}%"))
        
        if author: # if user searches with the author name
            statement = statement.where(Book.author.ilike(f"%{author}%"))
        
        result = await session.exec(statement) # Exceuct the statement
        books = result.all() # save all result
        
        
        # |--- Raise Exception if no book is found ---|
        if not books:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No book matched the search criteria."
            )
            
        return books
            