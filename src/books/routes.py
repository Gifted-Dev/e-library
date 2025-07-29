from fastapi import APIRouter, status, Depends, UploadFile, File, Form, Request
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.worker import send_email_task, delete_book_file_from_storage_task
from src.auth.services import UserService
from src.db.main import get_session
from src.auth.utils import create_download_token, decode_token
from src.books.schemas import BookCreateModel, BookSearchModel, BookUpdateModel, DownloadLogPublicModel
from src.books.services import BookService
from src.auth.dependencies import AccessTokenBearer, RoleChecker, ensure_user_is_verified
from src.core.storage import get_storage_service 
from datetime import datetime
from typing import Optional, List
from src.config import Config
import os
from uuid import UUID


from src import version
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
    
    # |--- Check if uploaded file is a valid type ---|
    if not file.filename or not is_valid_extension(file.filename):
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Only PDF, EPUB, and MOBI are allowed.")

    
    # |--- Get the ID of the user that uploaded the file ---|
    user_id = token_details.get('user')['user_uid']
    user_id = UUID(user_id)
    
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
    display_name, file_locator, file_size = await storage_service.save_file(file)
    
    await book_service.save_book(book_data=book_data,
                                      file_url=file_locator,
                                      file_size=file_size,
                                      uploaded_by=user_id,
                                      session=session)

    return {
        "message": f"{display_name} has been saved",
        "book_title": book_data.title,
        "upload_date" : str(upload_date)
    }
    
# |---- Routes to get all the books ----|
@book_router.get("/all_books", dependencies=[Depends(role_checker)], response_model=List[BookSearchModel])
async def get_all_books(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    all_books = await book_service.get_all_books(skip, limit,session)
    # It's better to return an empty list with a 200 OK status if no books are found.
    # This is not an error, but a successful query with zero results.
    return all_books

# |---- Get a particular book ----|
@book_router.get("/{book_uid}", dependencies=[Depends(role_checker)], response_model=BookSearchModel)
async def get_book(book_uid: UUID, session: AsyncSession = Depends(get_session)):
    book = await book_service.get_book(book_uid, session)
    
    return book

# |---- Route to search for books ----|
@book_router.get("/search", dependencies=[Depends(role_checker)], response_model=List[BookSearchModel])
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
@book_router.post("/{book_uid}/request-download",
                    dependencies=[Depends(role_checker), Depends(ensure_user_is_verified)],
                    status_code=status.HTTP_202_ACCEPTED)
async def request_download_link(book_uid: UUID,
                        request: Request,
                        token_details: dict = Depends(AccessTokenBearer()),
                        session: AsyncSession = Depends(get_session)):
    
    # |--- Get the User ID from the AccessTokenBearer() ---|
    user_uid = UUID(token_details.get('user')['user_uid'])
    
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
        book_uid=str(book_uid) # Convert UUID to string for the token
    )
    
    # Using request.url_for is a robust way to build URLs. It avoids issues with
    # trailing slashes in the domain and automatically resolves the correct path
    # based on the route's name.
    download_path = request.url_for('download_book')
    base_url = Config.DOMAIN.rstrip('/')
    download_url = f"{base_url}{download_path}?token={book_request_token}"
    
    # Using await on send_email directly would block. By adding it as a background task,
    # we can send the 202 response immediately.
    send_email_task.delay(
        subject=f"Download Link for {book.title}",
        recipients=[user_email],
        template_body={"download_url": download_url, "book_title": book.title},
        template_name="download_link.html"
    )
        
    return {"message" : "A download link will be sent to your email shortly"}
    
# |---- Route to download file ----|
@book_router.get("/download", name="download_book")
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

    book = await book_service.get_book(UUID(book_uid), session)

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
@book_router.patch("/{book_uid}", response_model=BookSearchModel, dependencies=[Depends(admin_checker)])
async def update_book(book_uid: UUID, book_data: BookUpdateModel, session: AsyncSession = Depends(get_session)):
    # |---- Update Book Using the Book Service -----|
    book = await book_service.update_book(book_uid, book_data, session)

    return book

# |---- Route to delete book ---|
@book_router.delete("/{book_uid}", dependencies=[Depends(admin_checker)], status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_uid: UUID, session: AsyncSession = Depends(get_session)) -> None:
    # The service method now returns the file_url directly after deleting the DB record.
    file_url_to_delete = await book_service.delete_book_record(book_uid, session)
    
    if file_url_to_delete:
        delete_book_file_from_storage_task.delay(file_url_to_delete)


# |---- Route to get download logs ---|
@book_router.get("/download-logs", response_model=List[DownloadLogPublicModel], dependencies=[Depends(admin_checker)])
async def get_download_logs(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    logs = await book_service.get_download_logs(session, skip, limit)
    return logs