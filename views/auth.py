from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.auth.services import UserService
from src.db.main import get_session, AsyncSession
from src.core.exceptions import InvalidTokenError, UserNotFoundError

router = APIRouter()

# Use the centralized PROJECT_ROOT from config for consistency
from src.config import PROJECT_ROOT
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))
user_service = UserService()

@router.get("/auth/verify-email", response_class=HTMLResponse)
async def verify_email_page(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Renders a page that attempts to verify the user's email with the given token.
    This is the user-facing endpoint that the link in the email points to.
    """
    try:
        user = await user_service.verify_user_email(token, session)
        
        return templates.TemplateResponse("verification_result.html", {
            "request": request,
            "title": "Verification Successful",
            "success": True,
            "message": f"Thank you, {user.first_name}! Your email has been successfully verified. You can now log in."
        })
    except (InvalidTokenError, UserNotFoundError) as e:
        # If verification fails, show a user-friendly error message on the page.
        return templates.TemplateResponse("verification_result.html", {
            "request": request,
            "title": "Verification Failed",
            "success": False,
            "message": str(e)
        })