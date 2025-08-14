from fastapi import APIRouter, status, Depends, UploadFile, File, Form, BackgroundTasks, Request, Response
from fastapi.exceptions import HTTPException
from src.core.exceptions import ValidationError
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.services import UserService
from src.db.main import get_session
from src.auth.utils import create_download_token, decode_token
from src.books.schemas import BookCreateModel, BookSearchModel, BookUpdateModel, DownloadLogPublicModel
from src.books.services import BookService
from src.auth.dependencies import get_current_user, RoleChecker, ensure_user_is_verified, User
from src.core.storage import get_storage_service, delete_book_file_from_storage
from src.core.email import create_message, send_email
from datetime import datetime
from typing import Optional, List
from src.config import Config
from pathlib import Path
import os
from uuid import UUID


book_router = APIRouter()
role_checker = RoleChecker(['admin', 'user', 'superadmin'])

admin_detail = "This action requires administrator priviledges"
admin_checker = RoleChecker(['admin', 'superadmin'], admin_detail)

user_service = UserService()
book_service = BookService()

# Use the centralized PROJECT_ROOT from config for consistency
from src.config import PROJECT_ROOT
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".mobi"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def is_valid_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_image_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@book_router.post("/upload", dependencies=[Depends(admin_checker)])
async def upload_file(request: Request,
                    title: str = Form(...),
                    author: str = Form(...),
                    description: str = Form(...),
                    session : AsyncSession = Depends(get_session),
                    current_user: User = Depends(get_current_user),
                    file: UploadFile = File(...),
                    cover_image: Optional[UploadFile] = File(None)):
    try:
        """
        Upload a new book file with an optional cover image.

        Only administrators can upload books. Supports PDF, EPUB, and MOBI formats for books,
        and JPG, JPEG, PNG for cover images.
        """
        if not file.filename or not is_valid_extension(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Only PDF, EPUB, and MOBI are allowed.")

        cover_image_url = None
        storage_service = get_storage_service()
        if cover_image and cover_image.filename:
            if not is_valid_image_extension(cover_image.filename):
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported image format. Only JPG, JPEG, and PNG are allowed."
                )
            _, cover_image_url, _ = await storage_service.save_file(cover_image, folder="covers")

        user_id = current_user.uid

        book_data = BookCreateModel(title=title,
                                    author=author,
                                    description=description,
                                    uploaded_by=user_id)

        await book_service.confirm_book_exists(book_data, session)

        _, file_url, file_size = await storage_service.save_file(file)

        await book_service.save_book(book_data=book_data,
                                    file_url=file_url,
                                    file_size=file_size,
                                    cover_image_url=cover_image_url,
                                    uploaded_by=user_id,
                                    session=session)

        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": f"Book '{book_data.title}' has been successfully uploaded.",
            "type": "success"
        })
    except (HTTPException, ValidationError) as e:
        detail = e.detail if hasattr(e, 'detail') else str(e)
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": detail,
            "type": "danger"
        })
    
@book_router.get("/all_books", response_model=List[BookSearchModel])
async def get_all_books(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    """Get all books with pagination."""
    return await book_service.get_all_books(skip, limit, session)

# |---- Route to search for books ----|
@book_router.get("/search", response_model=List[BookSearchModel])
async def search_books(title: Optional[str] = None, author: Optional[str] = None, skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    """Search books by title or author."""
    if not title and not author:
        raise ValidationError("Please provide a title or an author to search.")
    return await book_service.search_book(title, author, skip, limit, session)

@book_router.get("/{book_uid}", response_model=BookSearchModel)
async def get_book(book_uid: str, session: AsyncSession = Depends(get_session)):
    """Get a specific book by its UUID."""
    return await book_service.get_book(book_uid, session)


# |---- Route to Download book ----|
@book_router.post("/{book_uid}/request-download",
                    dependencies=[Depends(role_checker), Depends(ensure_user_is_verified)],
                    status_code=status.HTTP_200_OK)
async def request_download_link(request: Request, book_uid: str, background_tasks: BackgroundTasks,
                        current_user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)):
    
    try:
        user_uid = str(current_user.uid)
        user_email = current_user.email
        
        book = await book_service.get_book(book_uid, session)
        
        storage_service = get_storage_service()
        
        if not book.file_url or not await storage_service.file_exists(book.file_url):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book file not found on the server"
            )
            
        await book_service.create_download_record(book_uid, user_uid, session)
        
        book_request_token = create_download_token(
            user_data={"user_uid": user_uid, "email": user_email},
            book_uid=book_uid
        )
        
        download_url = f"{Config.DOMAIN}/api/v1/books/download?token={book_request_token}"
        
        message = create_message(
            subject=f"Download Link for {book.title}",
            recipients=[user_email],
            template_body={"download_url": download_url, "book_title": book.title, "first_name": current_user.first_name}
        )
        
        await send_email(background_tasks, message, template_name="download_link.html")
            
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request, "message": "A download link has been sent to your email.", "type": "success"
        })
    except HTTPException as e:
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request, "message": e.detail, "type": "danger"
        })
    
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
@book_router.patch("/{book_uid}/update", dependencies=[Depends(admin_checker)])
async def update_book(
    request: Request,
    book_uid: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...),
    cover_image: Optional[UploadFile] = File(None)
):
    try:
        new_cover_image_url = None
        if cover_image and cover_image.filename:
            if not is_valid_image_extension(cover_image.filename):
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported image format. Only JPG, JPEG, and PNG are allowed."
                )
            storage_service = get_storage_service()
            _, new_cover_image_url, _ = await storage_service.save_file(cover_image, folder="covers")

        book_data = BookUpdateModel(title=title, author=author, description=description)
        
        old_cover_to_delete = await book_service.update_book(
            book_uid, book_data, session, new_cover_image_url=new_cover_image_url
        )

        if old_cover_to_delete:
            background_tasks.add_task(delete_book_file_from_storage, old_cover_to_delete)

        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": f"Book '{book_data.title}' has been successfully updated.",
            "type": "success"
        })
    except (HTTPException, ValidationError) as e:
        detail = e.detail if hasattr(e, 'detail') else str(e)
        return templates.TemplateResponse("partials/_alert.html", {"request": request, "message": detail, "type": "danger"})

# |---- Route to delete book ---|
@book_router.delete("/delete-book/{book_uid}", dependencies=[Depends(admin_checker)])
async def delete_book(book_uid:str, background_tasks: BackgroundTasks, session:AsyncSession = Depends(get_session)):
    # The service method now returns both the book file URL and the cover image URL.
    file_url_to_delete, cover_image_url_to_delete = await book_service.delete_book(book_uid, session)

    # The slow/unreliable part runs in the background after the response has been sent.
    background_tasks.add_task(delete_book_file_from_storage, file_url_to_delete)
    if cover_image_url_to_delete:
        background_tasks.add_task(delete_book_file_from_storage, cover_image_url_to_delete)

    response = Response(status_code=status.HTTP_200_OK)
    response.headers["HX-Redirect"] = "/books"
    return response


# |---- Route to get download logs ---|
@book_router.get("/download-logs", response_model=List[DownloadLogPublicModel], dependencies=[Depends(admin_checker)])
async def get_download_logs(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    logs = await book_service.get_download_logs(session, skip, limit)
    return logs
