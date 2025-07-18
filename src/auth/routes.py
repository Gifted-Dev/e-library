# |---- Dependencies Needed ----|

# Import APIRouter
# Import UserService
# Import responseMondel, UserCreateModel
# import get_session from db.main




from fastapi import APIRouter, status, Depends
from src.auth.services import UserService
from src.auth.schemas import UserCreateModel, UserModel, UserLoginModel
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from src.config import Config
from src.auth.dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    get_current_user,
    RoleChecker
)
from src.auth.utils import create_access_token
from datetime import datetime

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['user', 'admin', 'superadmin'])

@auth_router.post("/signup", response_model= UserModel, status_code=status.HTTP_201_CREATED)


async def register_user(user_data: UserCreateModel, session:AsyncSession = Depends(get_session)):
    
    # |---- Check if user exists before creating user ----|
    
    # get user email
    email = user_data.email
    
    # check if email exists
    user_exists = await user_service.get_user_by_email(email, session)

    
    # return exception error if user exists
    if user_exists:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail="User with email already exists"
        )
    
    #create the user
    new_user = await user_service.create_user(user_data, session)
    
    # |---- Check if email is a superadmin ----|
    superadmin_emails = Config.SUPERADMIN_EMAILS
    
    # |---- Assign superadmin role to user ----|
    if email in superadmin_emails:
        new_user.role = "superadmin"
        await session.commit()
    
    # return the user
    return new_user

@auth_router.post("/login", response_model=UserModel, status_code=status.HTTP_202_ACCEPTED)
async def login_user(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    login = await user_service.login_user(login_data, session)
    return login


# To generate new access token 
@auth_router.get("/refresh")
async def get_new_access_token(
    token_details: dict = Depends(RefreshTokenBearer())
):
    
    # check for token expiry first
    token_expiry = token_details['exp']
    
    # check if it is past the expiry date
    if datetime.fromtimestamp(token_expiry) > datetime.now():
        new_access_token = create_access_token(user_data=token_details['user'])
        return JSONResponse(content={"access_token": new_access_token})
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            token_details="Invalid or expired token"
        )
        
    