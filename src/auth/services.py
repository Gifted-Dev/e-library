from src.db.models import User
from src.auth.schemas import UserCreateModel, UserLoginModel, UserUpdateModel
from src.auth.utils import (
    generate_password_hash, 
    verify_password,
    create_access_token)
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi import status
from sqlmodel import select
from datetime import timedelta, datetime
from uuid import UUID

#|---- Create a User Service Class that performs routes functions ----|
class UserService:
    # |---- get user by email ----|
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        
        result = await session.exec(statement)
        
        user = result.first()
        
        return user # This will now correctly return the user object or None
    
    
    # |---- check if user exists ----|
    async def user_exists(self, email:str, session:AsyncSession):
        user = await self.get_user_by_email(email, session)
        return True if user is not None else False
    
    # |---- create a user ----|
    async def create_user(self, user_data: UserCreateModel, session:AsyncSession):
        #convert the user data to a dic
        user_data_dict = user_data.model_dump()
        
        # Upack the data and create a new user instance
        new_user = User(**user_data_dict)
        
        # Hash Password
        new_user.password_hash = generate_password_hash(user_data_dict['password'])
        new_user.role = "user"
        
        # Add the user to session
        session.add(new_user)
        await session.commit()
        
        return new_user
    
    
    async def login_user(self, login_data: UserLoginModel, session:AsyncSession):
        # check if user exists
        email = login_data.email # get the user email
        user = await self.get_user_by_email(email, session)
        
        # This is the correct place to check if the user exists for login.
        if not user:
            raise HTTPException(    
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not exist, signup to login"
            )
        
        # if user exists, verify password
        validated = verify_password(login_data.password, user.password_hash)
       
        if validated:
            # create access token and refresh if password is valid
            access_token = create_access_token(
                user_data={"email": user.email, 
                           "user_uid": str(user.uid),
                           "role": user.role}
            )
            
            refresh_token = create_access_token(
                user_data={"email": user.email, 
                           "user_uid": str(user.uid),
                           },
                refresh=True,
                expiry=timedelta(days=2)
            )
            
            return JSONResponse(content={
                "message": "Login Successful",
                "access_token": access_token,
                "refresh_token": refresh_token
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Password!"
            )

        # |----Get My Profile ----|
    async def get_user_by_uid(self, user_uid: str, session:AsyncSession):
        
        # Convert user uid to UUID
        user_uid = UUID(user_uid)
        
        # Statement to request user by uid and execute
        statement = select(User).where(User.uid == user_uid)
        result = await session.exec(statement)
        user = result.first()
        
        # It's good practice for service methods to handle the "not found" case.
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with UID {user_uid} not found."
            )
            
        return user
    
    # |---- Model to allow User update their Profile ----|
    async def update_user(self, user_to_update: User, update_data: UserUpdateModel, session: AsyncSession):
        # The user object is passed directly from the route, no need to fetch it again.

        # Convert data to dict
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(user_to_update, key, value)
        
        session.add(user_to_update)
        await session.commit()
        await session.refresh(user_to_update)
        
        return user_to_update