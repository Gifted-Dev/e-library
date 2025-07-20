from fastapi import APIRouter, status, Depends, UploadFile, File, Form
from fastapi.exceptions import HTTPException
# from fastapi.responses import JSONResponse, FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.services import UserService
from src.db.main import get_session
from src.books.schemas import BookCreateModel, BookSearchModel
from src.books.services import BookService
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from src.core.storage import get_storage_service
from datetime import datetime
from typing import Optional, List
import os
import aiofiles


book_router = APIRouter()
role_checker = Depends(RoleChecker(['admin', 'user', 'superadmin']))
admin_checker = Depends(RoleChecker(['admin']))

user_service = UserService()
book_service = BookService()

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".mobi"}

def is_valid_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@book_router.post("/upload", dependencies=[admin_checker])
async def upload_file(title: str = Form(...),
                      author: str = Form(...),
                      description: str = Form(...),
                      session : AsyncSession = Depends(get_session),
                      token_details: dict = Depends(AccessTokenBearer()),
                      file: UploadFile = File(...)):
    
    # |--- Check if uploaded file is a valid type ---|
    valid_extension = is_valid_extension(file.filename)
    
    # |--- Raise Exception if file is not valid ---|
    if not valid_extension:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Only PDF, EPUB, and MOBI are allowed.")

    
    # |--- Get the ID of the user that uploaded the file ---|
    user_id = token_details.get('user')['user_uid']
    
    
    # |---- Get Upload_date ---|
    upload_date = datetime.now()
    
    
    # |--- Create Book data ---|
    book_data = BookCreateModel(title=title,
                                author=author,
                                description=description,
                                upload_date=upload_date,
                                uploaded_by=user_id)
    
    
    # |--- Check if file had been previously uploaded ---|
    await book_service.confirm_book_exists(book_data, session)


    # Save file using chosen backend
    storage_service = get_storage_service()
    filename, file_url, file_size = await storage_service.save_file(file)
    
    await book_service.save_book(book_data=book_data,
                                      file_url=file_url,
                                      file_size=file_size,
                                      uploaded_by=user_id,
                                      session=session)

    return {
        "message": f"{filename} has been saved",
        "book_title": book_data.title,
        "upload_date" : str(upload_date)
    }
    
# |---- Routes to get all the books ----|
@book_router.get("/all_books", dependencies=[role_checker], response_model=List[BookSearchModel])
async def get_all_books(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    all_books = await book_service.get_all_books(skip, limit,session)
    # It's better to return an empty list with a 200 OK status if no books are found.
    # This is not an error, but a successful query with zero results.
    return all_books

# |---- Get a particular book ----|
@book_router.get("/get_book", dependencies=[role_checker], response_model=BookSearchModel)
async def get_book(book_uid: str, session: AsyncSession = Depends(get_session)):
    book = await book_service.get_book(book_uid, session)
    
    return book

# |---- Route to search for books ----|
@book_router.get("/search", dependencies=[role_checker], response_model=List[BookSearchModel])
async def search_books(title: Optional[str] = None, author: Optional[str] = None, skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    # If the user doesn't provide any search terms, it's best to give them
    # a clear error instead of returning the entire list of books.
    if not title and not author:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a title or an author to search."
        )
    books = await book_service.search_book(title, author, skip, limit, session)
    
    return books


# |---- Route to Download book ----|
@book_router.get("/{book_uid}/download", dependencies=[role_checker])
async def download_book(book_uid: str,
                        token_details: dict = Depends(AccessTokenBearer()),
                        session: AsyncSession = Depends(get_session)):
    
    # |--- Get the User ID from the AccessTokenBearer() ---|
    user_uid = token_details.get('user')['user_uid'] 
    
    book = await book_service.get_book(book_uid, session)
    
    # |--- Confirm if file exists on the server ----|
    if not await aiofiles.os.path.exists(book.file_url):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book file not found on the server"
        )
        
    await book_service.create_download_record(book_uid, user_uid, session)
    
    return {"message" : "A download link will be sent to your email shortly"}
    
               

# |---- Route to delete book ---|
@book_router.delete("/delete-book", dependencies=[admin_checker])
async def delete_book(book_uid:str, session:AsyncSession = Depends(get_session)):
    book = await book_service.delete_book(book_uid, session)
    
    return book