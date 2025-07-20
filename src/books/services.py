from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.schemas import BookCreateModel
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlmodel import select, desc
from src.db.models import Book, Downloads
from datetime import datetime
from typing import Optional
from uuid import UUID
import os
import aiofiles



    

class BookService:
    
    async def confirm_book_exists(self, book_data, session:AsyncSession):
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
        
        
    async def save_book(self, book_data: BookCreateModel,
                        file_url: str,
                        file_size: float,
                        uploaded_by: UUID,
                        session:AsyncSession):
        
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
        
    
    async def get_all_books(self, skip, limit, session:AsyncSession):
        # |--- Run statement to get all books ---|
        statement = select(Book).order_by(desc(Book.upload_date)).offset(skip).limit(limit)
        
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
    
    async def search_book(self, title: Optional[str], author: Optional[str], skip, limit, session:AsyncSession):
        # |--- Statement to check which the user search for ---|
        statement = select(Book)
        
        if title: # if user searches with the title
            statement = statement.where(Book.title.ilike(f"%{title}%"))
        
        if author: # if user searches with the author name
            statement = statement.where(Book.author.ilike(f"%{author}%"))
            
        # Apply pagination
        paginated_statement = statement.offset(skip).limit(limit)
        
        result = await session.exec(paginated_statement) # Exceuct the statement
        books = result.all() # save all result
        
        # If no books match, we return an empty list.
        # This is more consistent and easier for the client to handle than a 404 error.
        return books
    
    async def delete_book(self, book_uid: str, session:AsyncSession):
        # |---- select book by uid ----|
        book = await self.get_book(book_uid, session)
        
        # |---- Delete Book ----|
        if book.file_url and await aiofiles.os.path.exists(book.file_url): # Check if path exists
            try:
                await aiofiles.os.remove(book.file_url) # Remove book from local storage
            except Exception as e: # Raise exception error if failed to delete.
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete file:{e}"
                )
                
        # |---- Commit Changes ----|
        await session.delete(book)
        await session.commit()
        
        return {"message" : "Book has been deleted successfully."}
    
    async def create_download_record(self, book_uid: str, user_uid: str, session: AsyncSession):
        # Add book_uid and user_uid into download table
        new_download = Downloads(book_uid, user_uid)
        session.add(new_download)
        await session.commit()
        
        return new_download