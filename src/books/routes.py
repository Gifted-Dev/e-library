from fastapi import APIRouter, status, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.exceptions import HTTPException
from src.core.exceptions import ValidationError
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.services import UserService
from src.db.main import get_session
from src.auth.utils import create_download_token, decode_token
from src.books.schemas import BookCreateModel, BookSearchModel, BookUpdateModel, DownloadLogPublicModel
from src.books.services import BookService
from src.auth.dependencies import AccessTokenBearer, RoleChecker, ensure_user_is_verified
from src.core.storage import get_storage_service, delete_book_file_from_storage
from src.core.email import create_message, send_email
from datetime import datetime
from typing import Optional, List
from src.config import Config
import os
from uuid import UUID


book_router = APIRouter()
role_checker = RoleChecker(['admin', 'user', 'superadmin'])

admin_detail = "This action requires administrator priviledges"
admin_checker = RoleChecker(['admin', 'superadmin'], admin_detail)

user_service = UserService()
book_service = BookService()

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".mobi"}

def is_valid_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@book_router.post("/upload", dependencies=[Depends(admin_checker)])
async def upload_file(title: str = Form(...),
                      author: str = Form(...),
                      description: str = Form(...),
                      session : AsyncSession = Depends(get_session),
                      token_details: dict = Depends(AccessTokenBearer()),
                      file: UploadFile = File(...)):
    
    """
    Upload a new book file.

    Only administrators can upload books. Supports PDF, EPUB, and MOBI formats.
    """
    if not file.filename or not is_valid_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Only PDF, EPUB, and MOBI are allowed.")

    user_id = UUID(token_details.get('user')['user_uid'])

    book_data = BookCreateModel(title=title,
                                author=author,
                                description=description,
                                uploaded_by=user_id)

    await book_service.confirm_book_exists(book_data, session)

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
        "upload_date": str(datetime.now())
    }
    
@book_router.get("/all_books", dependencies=[Depends(role_checker)], response_model=List[BookSearchModel])
async def get_all_books(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    """Get all books with pagination."""
    return await book_service.get_all_books(skip, limit, session)

@book_router.get("/search", dependencies=[Depends(role_checker)], response_model=List[BookSearchModel])
async def search_books(title: Optional[str] = None, author: Optional[str] = None, skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    """Search books by title or author."""
    if not title and not author:
        raise ValidationError("Please provide a title or an author to search.")
    return await book_service.search_book(title, author, skip, limit, session)

@book_router.get("/{book_uid}", dependencies=[Depends(role_checker)], response_model=BookSearchModel)
async def get_book(book_uid: str, session: AsyncSession = Depends(get_session)):
    """Get a specific book by its UUID."""
    return await book_service.get_book(book_uid, session)


# |---- Route to Download book ----|
@book_router.post("/{book_uid}/request-download",
                    dependencies=[Depends(role_checker), Depends(ensure_user_is_verified)],
                    status_code=status.HTTP_202_ACCEPTED)
async def request_download_link(book_uid: str, background_tasks: BackgroundTasks,
                        token_details: dict = Depends(AccessTokenBearer()),
                        session: AsyncSession = Depends(get_session)):
    
    # |--- Get the User ID from the AccessTokenBearer() ---|
    user_uid = token_details.get('user')['user_uid'] 
    
    # |---- Get the User Email from Access Token ----|
    user_email = token_details.get('user')['email']
    
    
    book = await book_service.get_book(book_uid, session)
    
    storage_service = get_storage_service()
    
    # |--- Confirm if file exists on the server ----|
    if not book.file_url or not await storage_service.file_exists(book.file_url):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book file not found on the server"
        )
        
    await book_service.create_download_record(book_uid, user_uid, session)
    
    book_request_token = create_download_token(
        user_data={"user_uid" : user_uid,
                   "email" : user_email},
        book_uid=book_uid
    )
    
    # |--- Construct a secure URL with the token as a query parameter ----|
    download_url = f"{Config.DOMAIN}/books/download?token={book_request_token}"
    
    message = create_message(
        subject=f"Download Link for {book.title}",
        recipients=[user_email],
        template_body={"download_url": download_url, "book_title": book.title}
    )
    
    # Using await on send_email directly would block. By adding it as a background task,
    # we can send the 202 response immediately.
    await send_email(background_tasks, message, template_name="download_link.html")
        
    return {"message" : "A download link will be sent to your email shortly"}
    
# |---- Route to download file ----|
@book_router.get("/download")
async def download_book(token: str, session: AsyncSession = Depends(get_session)):
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired download token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    book_uid = token_data.get("book_uid")
    if not book_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is missing required information."
        )

    book = await book_service.get_book(book_uid, session)

    storage_service = get_storage_service()
    if not book.file_url or not await storage_service.file_exists(book.file_url):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book file not found on the server. It may have been moved or deleted."
        )

    # The storage service now returns the appropriate response directly,
    # handling both local files (FileResponse) and S3 redirects (RedirectResponse).
    return await storage_service.get_download_response(book.file_url)


# |------- Route to Update Book ----------|
@book_router.patch("/{book_uid}/update", response_model=BookSearchModel, dependencies=[Depends(admin_checker)])
async def update_book(book_uid: str, book_data: BookUpdateModel, session: AsyncSession = Depends(get_session)):
    # |---- Update Book Using the Book Service -----|
    book = await book_service.update_book(book_uid, book_data, session)

    return book

# |---- Route to delete book ---|
@book_router.delete("/delete-book/{book_uid}", dependencies=[Depends(admin_checker)], status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_uid:str, background_tasks: BackgroundTasks, session:AsyncSession = Depends(get_session)) -> None:
    # The service method now returns the file_url directly after deleting the DB record.
    file_url_to_delete = await book_service.delete_book(book_uid, session)

    # The slow/unreliable part runs in the background after the response has been sent.
    background_tasks.add_task(delete_book_file_from_storage, file_url_to_delete)


# |---- Route to get download logs ---|
@book_router.get("/download-logs", response_model=List[DownloadLogPublicModel], dependencies=[Depends(admin_checker)])
async def get_download_logs(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    logs = await book_service.get_download_logs(session, skip, limit)
    return logs