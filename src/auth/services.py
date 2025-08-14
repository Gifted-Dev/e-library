from src.db.models import User, Downloads
from src.auth.schemas import UserCreateModel, UserLoginModel, UserUpdateModel
from src.core.email import create_message, send_email
from src.config import Config
from src.auth.utils import (
    generate_password_hash,
    verify_password,
    create_access_token,
    create_verification_token)
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from fastapi_mail import MessageType
from fastapi import status
from sqlmodel import select, desc
from datetime import timedelta, datetime
from uuid import UUID
from src.core.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    DatabaseError,
    InvalidTokenError
)
from src.core.redis import get_redis_service
from src.auth.utils import decode_token
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service class for user-related operations."""

    async def get_user_by_email(self, email: str, session: AsyncSession):
        """Retrieve a user by email address."""
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()

    async def user_exists(self, email: str, session: AsyncSession):
        """Check if a user exists by email."""
        user = await self.get_user_by_email(email, session)
        return user is not None
    
    # |---- create a user ----|
    async def create_user(self, user_data: UserCreateModel, session:AsyncSession):
        #convert the user data to a dic
        user_data_dict = user_data.model_dump()

        # Upack the data and create a new user instance
        new_user = User(**user_data_dict)

        # Hash Password
        new_user.password_hash = generate_password_hash(user_data_dict['password'])
        new_user.role = "user"

        # Check if user should be superadmin
        if user_data.email in Config.SUPERADMIN_EMAILS:
            new_user.role = "superadmin"

        # Add the user to session
        session.add(new_user)
        await session.commit()

        return new_user
    
    async def verify_user_email(self, token: str, session: AsyncSession) -> User:
        """
        Verifies a user's email using a token, marks them as verified, and returns the user.
        Raises InvalidTokenError or UserNotFoundError on failure.
        """
        token_data = decode_token(token)
        if not token_data:
            raise InvalidTokenError("Invalid or expired verification token. Please request a new one.")

        email = token_data["user"]["email"]
        user = await self.get_user_by_email(email, session)

        if not user:
            raise UserNotFoundError("User associated with this token not found.")

        # Only commit to the database if the user is not already verified.
        if not user.is_verified:
            user.is_verified = True
            await session.commit()
            await session.refresh(user)
        
        return user

    
    async def login_user(self, login_data: UserLoginModel, session:AsyncSession):
        try:
            # check if user exists
            email = login_data.email # get the user email
            user = await self.get_user_by_email(email, session)

            # This is the correct place to check if the user exists for login.
            if not user:
                raise UserNotFoundError("User does not exist, please sign up first")

            # if user exists, verify password
            validated = verify_password(login_data.password, user.password_hash)

            if validated:
                # Check if the user's email is in the superadmin list and their role isn't already superadmin.
                # This promotes them upon login and persists the change.
                if email in Config.SUPERADMIN_EMAILS and user.role != "superadmin":
                    user.role = "superadmin"
                    session.add(user)
                    await session.commit()
                    await session.refresh(user) # Ensure the user object has the latest data
                    logger.info(f"User '{email}' promoted to superadmin upon login.")

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

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            else:
                raise InvalidCredentialsError("Invalid email or password")
        except Exception as e:
            if isinstance(e, (UserNotFoundError, InvalidCredentialsError)):
                raise
            raise DatabaseError("An error occurred during login")

        # |----Get My Profile ----|
    async def get_user_by_uid(self, user_uid: str, session:AsyncSession):
        try:
            # Convert user uid to UUID
            user_uid = UUID(user_uid)

            # Statement to request user by uid and execute
            statement = select(User).where(User.uid == user_uid)
            result = await session.exec(statement)
            user = result.first()

            # It's good practice for service methods to handle the "not found" case.
            if not user:
                raise UserNotFoundError(f"User with UID {user_uid} not found")

            return user
        except ValueError as e:
            raise ValueError(f"Invalid user ID format: {user_uid}")
        except Exception as e:
            if isinstance(e, UserNotFoundError):
                raise
            raise DatabaseError("An error occurred while fetching user")
    
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
    
    # |--- Function to change password ----|
    async def verification_logic(self, email, user, background_tasks):
        verification_token = create_verification_token(
            user_data={
                "email":email,
                "user_uid": str(user.uid) # Makes sure to convert uid to string
            }
        )
        
        verification_url = f"{Config.DOMAIN}/auth/verify-email?token={verification_token}"
        
        message = create_message(
            subject="Please verify your Email",
            recipients=[email],
            template_body={"verification_url": verification_url, "first_name": user.first_name}
        )
        
        await send_email(background_tasks, message, template_name="verify_email.html")
        
    async def get_all_users(self, session: AsyncSession, skip: int = 0, limit: int = 20):
        statement = select(User).order_by(desc(User.created_at)).offset(skip).limit(limit)
        
        result =  await session.exec(statement)
        
        return result.all()
    
    async def get_all_admins(self, session: AsyncSession, skip: int = 0, limit: int = 20):
        statement = select(User).where(User.role == 'admin').order_by(desc(User.created_at), desc(User.uid)).offset(skip).limit(limit)
        
        result =  await session.exec(statement)
        
        return result.all()
        
    async def get_user_download_history(self, user_id: str, session: AsyncSession, skip: int = 0, limit: int = 20):
        statement = select(Downloads).where(Downloads.user_id == user_id).order_by(desc(Downloads.timestamp)).offset(skip).limit(limit)

        result = await session.exec(statement)

        return result.all()

    async def logout_user(self, access_token_data: dict, refresh_token: Optional[str] = None) -> dict:
        """
        Handle user logout by invalidating tokens.

        Args:
            access_token_data: Decoded access token data
            refresh_token: Optional refresh token to invalidate

        Returns:
            dict: Success message

        Raises:
            HTTPException: If logout service is unavailable
        """
        from fastapi import HTTPException

        redis_service = await get_redis_service()

        # Check Redis availability
        if not await redis_service.is_connected():
            logger.error("Redis unavailable during logout attempt")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Logout service temporarily unavailable"
            )

        # Invalidate access token
        await self._invalidate_token(redis_service, access_token_data, "access")

        # Invalidate refresh token if provided
        if refresh_token:
            await self._invalidate_refresh_token(redis_service, refresh_token)

        logger.info(f"User {access_token_data.get('user', {}).get('email', 'unknown')} logged out successfully")
        return {"message": "Successfully logged out"}

    async def _invalidate_token(self, redis_service, token_data: dict, token_type: str) -> bool:
        """
        Invalidate a single token by adding it to blocklist.

        Args:
            redis_service: Redis service instance
            token_data: Decoded token data
            token_type: Type of token (access/refresh) for logging

        Returns:
            bool: True if token was invalidated successfully
        """
        jti = token_data.get("jti")
        exp = token_data.get("exp")

        if not jti or not exp:
            logger.warning(f"Missing JTI or expiration in {token_type} token")
            return False

        # Calculate remaining time until token expires
        remaining_time = max(0, exp - int(datetime.now().timestamp()))

        if remaining_time <= 0:
            logger.info(f"{token_type.capitalize()} token already expired, skipping blocklist")
            return True

        # Add to blocklist
        success = await redis_service.add_to_blocklist(jti, remaining_time)

        if success:
            logger.info(f"{token_type.capitalize()} token {jti[:8]}... added to blocklist")
        else:
            logger.error(f"Failed to add {token_type} token to blocklist")

        return success

    async def _invalidate_refresh_token(self, redis_service, refresh_token: str) -> bool:
        """
        Decode and invalidate refresh token.

        Args:
            redis_service: Redis service instance
            refresh_token: Raw refresh token string

        Returns:
            bool: True if token was invalidated successfully
        """
        try:
            refresh_token_data = decode_token(refresh_token)

            if not refresh_token_data:
                logger.warning("Invalid refresh token provided for logout")
                return False

            return await self._invalidate_token(redis_service, refresh_token_data, "refresh")

        except Exception as e:
            logger.error(f"Error processing refresh token during logout: {e}")
            return False