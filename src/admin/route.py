from fastapi import APIRouter, Form, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.auth.services import UserService
from src.auth.dependencies import RoleChecker

admin_router = APIRouter()
superadmin_checker = Depends(RoleChecker(['superadmin']))
user_service = UserService()



# |--- API to give admin access ---|
@admin_router.post("/make_admin", dependencies=[superadmin_checker])
async def make_admin(email: str = Form(...), session: AsyncSession = Depends(get_session)):
    # |----Use User service to get the user by mail ---|
    new_admin = await user_service.get_user_by_email(email, session)
    
    # |--- Confirm if user is previously an admin user ----|
    if new_admin.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has admin access"
        )
    
    # |--- Give admin role ----|
    new_admin.role = "admin"
    
    # Save Changes to DB
    await session.commit()
    
    return {"message": f"Admin role has been given to {new_admin.email}"}


# |---- API to give revoke access ---|
@admin_router.post("/revoke_admin", dependencies=[superadmin_checker])
async def revoke_admin(email:str = Form(...), session: AsyncSession = Depends(get_session)):
    # |--- User User_service to revoke user by mail ---|
    ex_admin = await user_service.get_user_by_email(email, session)
    
    
    # |--- Confirm is user is previous an admin user ----|
    if ex_admin.role != "admin":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "User does not have admin access"
        )
    
    # |--- Remove admin access ---|
    ex_admin.role = "user"
    
    # Save changes to DB
    await session.commit()
    
    return {"message" : f"Admin role has been revoked from {ex_admin.email}"}