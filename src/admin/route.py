from fastapi import APIRouter, Form, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.auth.schemas import UserPublicModel
from src.auth.services import UserService
from src.auth.dependencies import RoleChecker

admin_router = APIRouter()
superadmin_checker = RoleChecker(
    ['superadmin'], detail="This action requires super-administrator priviledges"
)
user_service = UserService()



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
    
    
    # |--- Confirm is user is previous an admin user ----|
    if user.role != "admin":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "User does not have admin access"
        )
    
    # |--- Remove admin access ---|
    user.role = "user"
    
    # Save changes to DB
    await session.commit()
    await session.refresh(user)
    
    return user