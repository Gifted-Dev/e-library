from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.schemas import BookCreateModel, BookUpdateModel
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlmodel import select, desc
from src.db.models import Book, Downloads
from datetime import datetime
from typing import Optional
from src.core.storage import get_storage_service
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
    
    
    async def update_book(self, book_uid: str, book_data: BookUpdateModel, session:AsyncSession):
        # |---- Get the book using the book_uid ---|
        # `get_book` is an async function and must be awaited.
        book = await self.get_book(book_uid, session)
        
        # Use model_dump to get a dictionary of the provided data, excluding unset fields.
        # This ensures we only update the fields the user actually sent.
        update_data = book_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(book, key, value)
        
        session.add(book)
        await session.commit()
        await session.refresh(book)
        
        return book
        
    
    async def delete_book(self, book_uid: str, session:AsyncSession) -> None:
        # |---- select book by uid ----|
        book = await self.get_book(book_uid, session)
        
        storage_service = get_storage_service()
        # |---- Delete Book ----|
        # Use the storage abstraction to check for file existence
        if book.file_url and await storage_service.file_exists(book.file_url):
            try:
                await storage_service.delete_file(book.file_url)
            except Exception as e: # Raise exception error if failed to delete.
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete file:{e}"
                )
                
        # |---- Commit Changes ----|
        await session.delete(book)
        await session.commit()
        
        return None
    
    async def create_download_record(self, book_uid: str, user_uid: str, session: AsyncSession):
        # Convert string UIDs to UUID objects, as the database model expects.
        book_id_uuid = UUID(book_uid)
        user_id_uuid = UUID(user_uid)
        
        # Create a new download record using keyword arguments for clarity and safety.
        new_download = Downloads(book_id=book_id_uuid, user_id=user_id_uuid)
        session.add(new_download)
        await session.commit()
        # Refresh the object to get default values from the DB, like the timestamp.
        await session.refresh(new_download)
        
        return new_download