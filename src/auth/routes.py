# |---- Dependencies Needed ----|

# Import APIRouter
# Import UserService
# Import responseMondel, UserCreateModel
# import get_session from db.main




from fastapi import APIRouter, status, Depends, BackgroundTasks
from src.auth.services import UserService
from src.auth.schemas import (UserCreateModel,
                              UserPublicModel,
                              UserLoginModel,
                              UserUpdateModel,
                              UserDownloadHistoryModel,
                              ForgotPasswordSchema,
                              ResetPasswordSchema,
                              PasswordChangeSchema,
                              LogoutSchema)
from src.auth.utils import create_verification_token, create_password_reset_token, verify_password, generate_password_hash
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
    AccessTokenBearer,
    get_current_user,
    RoleChecker,
    User
)

from fastapi_mail import MessageType
from src.auth.utils import create_access_token, decode_token
from datetime import datetime
from typing import List

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['user', 'admin', 'superadmin'])



@auth_router.post("/signup", response_model=UserPublicModel, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreateModel, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    """
    Register a new user account.

    Creates a new user with email verification and automatic superadmin assignment
    if the email is in the configured superadmin list.
    """
    email = user_data.email

    user_exists = await user_service.get_user_by_email(email, session)
    if user_exists:
        raise UserAlreadyExistsError(email)

    new_user = await user_service.create_user(user_data, session)
    await user_service.verification_logic(email, new_user, background_tasks)

    return new_user

@auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str, session: AsyncSession = Depends(get_session)):
    """
    Verify user email address using verification token.

    Decodes the verification token and marks the user as verified.
    """
    token_data = decode_token(token)
    if not token_data:
        raise InvalidTokenError("Invalid or expired verification token")

    email = token_data["user"]["email"]
    user = await user_service.get_user_by_email(email, session)

    if not user:
        raise UserNotFoundError("This user's email is not found")

    user.is_verified = True
    await session.commit()
    await session.refresh(user)

    return {"message": "Your email has been successfully verified"}
 
@auth_router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """
    Resend email verification link to user.

    Only works for users who are not already verified.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already verified"
        )

    await user_service.verification_logic(current_user.email, current_user, background_tasks)
    return {"message": "A new verification email has been sent."}
    
    

@auth_router.post("/login", status_code=status.HTTP_202_ACCEPTED)
async def login_user(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    # The user service handles the entire login flow: finding the user,
    # checking for verification, verifying the password, and creating tokens.
    login = await user_service.login_user(login_data, session)
    return login

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
        
@auth_router.post("/forgot-password")
async def forgot_password(user_data: ForgotPasswordSchema, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    """This route is used to send the user a password reset link"""
    
    # 1. First we get the user email
    email = user_data.email
    
    # 2. we get the user, to confirm if the user exists
    user = await user_service.get_user_by_email(email, session)

    # Always return the same message to prevent email enumeration attacks
    response_message = "If an account with email exists, a password reset link has been sent"

    # confirming if user exists
    if not user:
        return {"message": response_message}

    
    # 3. Create a message and verification token that will be sent to the user
    password_reset_token = create_password_reset_token(
        user_data={"email" : email,
                   "user_uid": str(user.uid)
                   }
    )
    
    # This link should point to your frontend application.
    reset_link = f"{Config.DOMAIN}/reset-password?token={password_reset_token}"
    
    message = create_message(
        subject="Password Reset Request",
        recipients=[email],
        template_body={"reset_link": reset_link, "first_name": user.first_name},
    )
    
    # 4. Use background task to send the message
    await send_email(background_tasks, message, template_name="reset_password.html")

    return {"message": response_message}

# |--- Route to reset password ---|
@auth_router.post("/reset-password", status_code=status.HTTP_202_ACCEPTED)
async def reset_password(token: str, password_data:ResetPasswordSchema, session:AsyncSession = Depends(get_session)):
    
    # fetch the token
    token_data = decode_token(token)

    # check if the token is valid
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired password reset token"
        )
    
    # fetch the user details from token
    user_uid = token_data["user"]["user_uid"]
    user = await user_service.get_user_by_uid(user_uid, session)
    
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user does not exist in our database"
        )
        
    password_reset = password_data.password
    confirm_password_reset = password_data.confirm_password
    
    if password_reset != confirm_password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The passwords are not the same"
        )
    
    # generate new password hash
    new_password = password_data.password
    new_password_hash = generate_password_hash(new_password)
    
    # Update the user password
    user.password_hash = new_password_hash
    
    await session.commit()
    await session.refresh(user)
    
    return {
        "message" : "Password reset was successful"
    }



# |--- Route to change user password ---|
@auth_router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user_data:PasswordChangeSchema,
                         current_user: User = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)
                         ):
    
    # get the user old and new password
    old_password = user_data.old_password
    
    # check if user old password is correct
    verification_successful = verify_password(old_password, current_user.password_hash)
    
    if not verification_successful:
        raise InvalidCredentialsError("Invalid Password")
        
    # get new password
    new_password = user_data.new_password
    new_password_hash = generate_password_hash(new_password)
    
    # update the user_password
    current_user.password_hash = new_password_hash
    
    await session.commit()
    await session.refresh(current_user)
    
    return None

@auth_router.get("/users/me/downloads", response_model=List[UserDownloadHistoryModel])
async def get_downloads(current_user : User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session),
                        skip: int = 0, limit: int = 20):
   return await user_service.get_user_download_history(current_user.uid, session, skip, limit)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    logout_data: LogoutSchema,
    access_token_data: dict = Depends(AccessTokenBearer())
):
    """
    Logout user by invalidating tokens.

    Invalidates both access and refresh tokens by adding their JTIs to Redis blocklist.
    The refresh token should be provided in the request body as JSON: {"refresh_token": "..."}
    """
    return await user_service.logout_user(
        access_token_data=access_token_data,
        refresh_token=logout_data.refresh_token
    )