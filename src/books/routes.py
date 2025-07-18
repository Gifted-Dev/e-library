from fastapi import APIRouter, status, Depends, UploadFile, File, Form
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.services import UserService
from src.db.main import get_session
from src.books.schemas import BookCreateModel
from src.books.services import BookService
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from src.core.storage import get_storage_service
from datetime import datetime
import uuid
import os


book_router = APIRouter()
role_checker = Depends(RoleChecker(['admin', 'user', 'superadmin']))
superadmin_checker = Depends(RoleChecker(['superadmin']))

user_service = UserService()
book_service = BookService()

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".mobi"}

def is_valid_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@book_router.post("/upload", dependencies=[superadmin_checker])
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
                                uploadedby=user_id)
    
    
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