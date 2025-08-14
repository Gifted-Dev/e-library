# |---- Dependencies Needed ----|

from pathlib import Path
from fastapi import (
    APIRouter, status, Depends, BackgroundTasks, Form, Request, Response
)
from fastapi.templating import Jinja2Templates
from src.auth.services import UserService
from src.auth.schemas import (UserCreateModel,
                            UserPublicModel,
                            UserLoginModel,
                            UserUpdateModel,
                            UserDownloadHistoryModel,
                            PasswordChangeSchema)
from src.auth.utils import create_password_reset_token, verify_password, generate_password_hash
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.config import Config
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from src.core.email import create_message, send_email
from src.core.exceptions import (
    UserAlreadyExistsError,
    InvalidTokenError,
    UserNotFoundError,
    ValidationError,
    InvalidCredentialsError
)
from src.auth.dependencies import (
    RefreshTokenBearer,
    get_current_user,
    get_validated_token_data,
    User
)

from src.auth.utils import create_access_token, decode_token
from datetime import datetime
from typing import List, Optional

auth_router = APIRouter()
user_service = UserService()

# Define the project's base directory and point to the root templates folder
# This ensures that the path to templates is always correct, regardless of where the app is run from.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@auth_router.post("/signup", status_code=status.HTTP_200_OK)
async def register_user(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    first_name: str = Form(..., alias="signupFirstName"),
    last_name: str = Form(..., alias="signupLastName"),
    email: str = Form(..., alias="signupEmail"),
    password: str = Form(..., alias="signupPassword")
):
    """
    Register a new user account.

    Creates a new user with email verification and automatic superadmin assignment
    if the email is in the configured superadmin list.
    """
    try:
        user_data = UserCreateModel(
            first_name=first_name, last_name=last_name, email=email, password=password
        )
        user_exists = await user_service.get_user_by_email(email, session)
        if user_exists:
            raise UserAlreadyExistsError(email)

        new_user = await user_service.create_user(user_data, session)
        await user_service.verification_logic(email, new_user, background_tasks)

        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": "Signup successful! A verification email has been sent.",
            "type": "success"
        })
    except (UserAlreadyExistsError, ValidationError) as e:
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request, "message": str(e), "type": "danger"
        })

@auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str, session: AsyncSession = Depends(get_session)):
    """
    Verify user email address using verification token. (API endpoint)

    Decodes the verification token and marks the user as verified.
    """
    try:
        await user_service.verify_user_email(token, session)
        return {"message": "Your email has been successfully verified"}
    except (InvalidTokenError, UserNotFoundError) as e:
        # Re-raise as an HTTPException for API consumers, which our error handler will catch.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
 
@auth_router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Resend email verification link to user. Returns an HTML partial.
    Only works for users who are not already verified.
    """
    if current_user.is_verified:
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request, "message": "This account is already verified.", "type": "info"
        })

    await user_service.verification_logic(current_user.email, current_user, background_tasks)
    
    return templates.TemplateResponse("partials/_alert.html", {
        "request": request, "message": "A new verification email has been sent.", "type": "success"
    })
    
    
@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
    email: str = Form(..., alias="loginEmail"),
    password: str = Form(..., alias="loginPassword")
):
    try:
        login_data = UserLoginModel(email=email, password=password)
        tokens = await user_service.login_user(login_data, session)

        # Create a response object to set cookies and headers.
        # This avoids conflicts with exception handlers.
        response = Response()
        response.set_cookie(
            key="access_token",
            value=f"Bearer {tokens['access_token']}",
            httponly=True,
            samesite="lax",
            secure=Config.ENVIRONMENT != "development",
            path="/"
        )
        # This header tells HTMX to do a full page refresh on success
        response.headers["HX-Refresh"] = "true"
        return response

    except (UserNotFoundError, InvalidCredentialsError) as e:
        # On failure, return an alert partial to the modal
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": str(e),
            "type": "danger"
        })

# |----Route for user to check their Profile ----|
@auth_router.get("/users/me", response_model=UserPublicModel)
async def get_me(current_user: User = Depends(get_current_user)):
    # The `get_current_user` dependency already fetches the user object from the DB.
    # All we need to do is return it. FastAPI will filter it through the response_model.
    return current_user


# |--- Route for user to update their profile ----|
@auth_router.patch("/users/me", response_model=UserPublicModel)
async def update_me(
    update_data: UserUpdateModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # The `get_current_user` dependency provides the user object to be updated.
    # Pass the user object from the dependency directly to the service.
    
    updated_user = await user_service.update_user(current_user, update_data, session)
    
    return updated_user

# To generate new access token 
@auth_router.get("/refresh")
async def get_new_access_token(
    token_details: dict = Depends(RefreshTokenBearer())
):
    """# This endpoint takes a valid refresh token and issues a new, short-lived access token,
    # allowing the user to stay logged in without re-entering their password."""
    
    # check for token expiry first
    token_expiry = token_details['exp']
    
    # check if it is past the expiry date
    if datetime.fromtimestamp(token_expiry) > datetime.now():
        new_access_token = create_access_token(user_data=token_details['user'])
        return JSONResponse(content={"access_token": new_access_token})
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token"
        )
        
@auth_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    email: str = Form(...)
):
    """This route is used to send the user a password reset link"""
    user = await user_service.get_user_by_email(email, session)

    # Always return the same message to prevent email enumeration attacks
    response_message = "If an account with that email exists, a password reset link has been sent."

    if user:
        password_reset_token = create_password_reset_token(
            user_data={"email": email, "user_uid": str(user.uid)}
        )
        
        reset_link = f"{Config.DOMAIN}/reset-password?token={password_reset_token}"
        
        message = create_message(
            subject="Password Reset Request",
            recipients=[email],
            template_body={"reset_link": reset_link, "first_name": user.first_name},
        )
        
        await send_email(background_tasks, message, template_name="reset_password_email.html")

    return templates.TemplateResponse("partials/_alert.html", {
        "request": request,
        "message": response_message,
        "type": "success"
    })

# |--- Route to reset password ---|
@auth_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_session),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    try:
        token_data = decode_token(token)
        if not token_data:
            raise InvalidTokenError("Invalid or expired password reset token.")

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        user_uid = token_data["user"]["user_uid"]
        user = await user_service.get_user_by_uid(user_uid, session)

        if not user:
            raise UserNotFoundError("User not found.")

        new_password_hash = generate_password_hash(password)
        user.password_hash = new_password_hash
        await session.commit()

        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": 'Password reset successful! You can now <a href="#" data-bs-toggle="modal" data-bs-target="#loginModal" class="alert-link">log in</a>.',
            "type": "success"
        })
    except (InvalidTokenError, ValidationError, UserNotFoundError) as e:
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request,
            "message": str(e),
            "type": "danger"
        })



# |--- Route to change user password ---|
@auth_router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    try:
        # check if user old password is correct
        verification_successful = verify_password(old_password, current_user.password_hash)
        
        if not verification_successful:
            raise InvalidCredentialsError("The current password you entered is incorrect.")
            
        # get new password and hash it
        new_password_hash = generate_password_hash(new_password)
        
        # update the user_password
        current_user.password_hash = new_password_hash
        
        await session.commit()
        
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request, "message": "Your password has been updated successfully.", "type": "success"
        })
    except InvalidCredentialsError as e:
        return templates.TemplateResponse("partials/_alert.html", {
            "request": request, "message": str(e), "type": "danger"
        })

@auth_router.get("/users/me/downloads", response_model=List[UserDownloadHistoryModel])
async def get_downloads(current_user : User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session),
                        skip: int = 0, limit: int = 20):
   return await user_service.get_user_download_history(current_user.uid, session, skip, limit)


@auth_router.post("/logout")
async def logout_user(
    access_token_data: Optional[dict] = Depends(get_validated_token_data)
):
    """
    Logout user by invalidating access token and clearing the auth cookie.
    """
    # Create a response object to manipulate. This avoids conflicts with exception handlers.
    response = Response()

    if access_token_data:
        await user_service.logout_user(access_token_data=access_token_data)

    # Clear the cookie
    response.delete_cookie("access_token")

    # This header tells HTMX to redirect to the home page
    response.headers["HX-Redirect"] = "/"

    # Return the response with the cookie cleared and redirect header
    return response