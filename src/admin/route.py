from fastapi import APIRouter, Form, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.auth.schemas import UserPublicModel
from src.auth.services import UserService
from src.books.services import BookService
from src.books.schemas import DownloadLogPublicModel
from src.auth.dependencies import RoleChecker
from typing import List

admin_router = APIRouter()
superadmin_checker = RoleChecker(
    ['superadmin'], detail="This action requires super-administrator priviledges"
)
admin_checker = RoleChecker(['admin', 'superadmin'])
user_service = UserService()
book_service = BookService()


# |--- API to give admin access ---|
@admin_router.post("/make_admin", dependencies=[Depends(superadmin_checker)], response_model=UserPublicModel)
async def make_admin(email: str = Form(...), session: AsyncSession = Depends(get_session)):
    # |----Use User service to get the user by mail ---|
    user = await user_service.get_user_by_email(email, session)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email Not Found"
        )
    
    # |--- Confirm if user is previously an admin user ----|
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has admin access"
        )
    
    # |--- Give admin role ----|
    user.role = "admin"
    
    # Save Changes to DB
    await session.commit()
    await session.refresh(user)
    
    return user

# |---- API to give revoke access ---|
@admin_router.post("/revoke_admin", dependencies=[Depends(superadmin_checker)], response_model=UserPublicModel)
async def revoke_admin(email:str = Form(...), session: AsyncSession = Depends(get_session)):
    # |--- User User_service to revoke user by mail ---|
    user = await user_service.get_user_by_email(email, session)
    
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email Not Found"
        )
    
    # |--- Confirm the user is an admin before revoking privileges ----|
    # This prevents trying to revoke from a 'superadmin' or a regular 'user'.
    if user.role != "admin":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "This user is not an admin."
        )
    
    # |--- Remove admin access ---|
    user.role = "user"
    
    # Save changes to DB
    await session.commit()
    await session.refresh(user)
    
    return user

# |---- API to list all Users ---|
@admin_router.get("/users", response_model=List[UserPublicModel], dependencies=[Depends(admin_checker)], status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    return await user_service.get_all_users(session, skip, limit)
    
@admin_router.get("/admins", response_model=List[UserPublicModel], dependencies=[Depends(superadmin_checker)], status_code=status.HTTP_200_OK)
async def get_all_admins(skip: int = 0, limit: int = 20, session: AsyncSession = Depends(get_session)):
    return await user_service.get_all_admins(session, skip, limit)

@admin_router.get("/downloads", response_model=List[DownloadLogPublicModel], dependencies=[Depends(admin_checker)])
async def get_downloads(skip: int = 0, limit: int =20, session: AsyncSession = Depends(get_session)):
    return await book_service.get_download_logs(session, skip, limit)