from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.books.services import BookService
from src.auth.services import UserService
from src.db.main import get_session, AsyncSession
from src.auth.dependencies import get_current_user_or_none, get_current_user, User, RoleChecker
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter()
admin_checker = RoleChecker(['admin', 'superadmin'])

# Define the project's base directory and point to the root templates folder
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
book_service = BookService()
user_service = UserService()


@router.get("/", response_class=HTMLResponse)
async def base(request: Request, current_user: Optional[User] = Depends(get_current_user_or_none)):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "title": "Home - LightBearers Library",
        "current_user": current_user
    })

@router.get("/books", response_class=HTMLResponse)
async def all_books_page(
    request: Request,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_or_none)
):
    """Serves the page that lists all books, with optional search functionality."""
    if search:
        # If a search term is provided, use the search service
        books = await book_service.search_book(title=search, author=search, skip=0, limit=50, session=session)
    else:
        # Otherwise, get all books
        books = await book_service.get_all_books(skip=0, limit=50, session=session)

    # Check if the request is from HTMX
    if "HX-Request" in request.headers:
        # If it's an HTMX request, return only the partial
        return templates.TemplateResponse("partials/_book_list.html", {"request": request, "books": books})
    
    # For a normal page load, return the full page
    return templates.TemplateResponse("books.html", {
        "request": request, "books": books, "title": "Our Collection", "current_user": current_user
    })

@router.get("/books/{book_uid}", response_class=HTMLResponse)
async def book_detail_page(
    request: Request,
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_or_none)
):
    """Serves the detail page for a single book."""
    book = await book_service.get_book(book_uid, session)
    return templates.TemplateResponse("book_detail.html", {
        "request": request, "book": book, "title": book.title, "current_user": current_user
    })

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, current_user: Optional[User] = Depends(get_current_user_or_none)):
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "title": "Sign Up - LightBearers Library",
        "current_user": current_user
    })

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request, current_user: Optional[User] = Depends(get_current_user_or_none)):
    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "title": "Forgot Password - LightBearers Library",
        "current_user": current_user
    })

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = Query(...), current_user: Optional[User] = Depends(get_current_user_or_none)):
    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "title": "Reset Password - LightBearers Library",
        "current_user": current_user,
        "token": token
    })

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Serves the user's profile page, showing account details and download history."""
    download_history = await user_service.get_user_download_history(current_user.uid, session)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "title": "My Profile",
        "current_user": current_user,
        "download_history": download_history
    })

@router.get("/admin", response_class=HTMLResponse, dependencies=[Depends(admin_checker)])
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Serves the admin dashboard page."""
    all_users = await user_service.get_all_users(session, limit=100) # Fetch a reasonable number for the dashboard
    download_logs = await book_service.get_download_logs(session, limit=100)

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "title": "Admin Dashboard",
        "current_user": current_user,
        "users": all_users,
        "download_logs": download_logs
    })

@router.get("/admin/upload-book", response_class=HTMLResponse, dependencies=[Depends(admin_checker)])
async def admin_upload_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Serves the page for admins to upload new books."""
    return templates.TemplateResponse("admin_upload.html", {
        "request": request, "title": "Upload Book", "current_user": current_user
    })

@router.get("/admin/edit-book/{book_uid}", response_class=HTMLResponse, dependencies=[Depends(admin_checker)])
async def admin_edit_book_page(
    request: Request,
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Serves the page for admins to edit an existing book."""
    book = await book_service.get_book(book_uid, session)
    return templates.TemplateResponse("admin_edit_book.html", {
        "request": request,
        "title": f"Edit {book.title}",
        "current_user": current_user,
        "book": book
    })