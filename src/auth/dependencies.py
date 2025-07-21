from fastapi.security import HTTPBearer
from fastapi import Request, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials
from src.auth.utils import decode_token
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.auth.services import UserService
from src.db.models import User
from typing import List


user_service = UserService()

class TokenBearer(HTTPBearer):
    async def __call__(self, request: Request) -> dict:
        credentials = await super().__call__(request)
        token = credentials.credentials
        token_data = decode_token(token)

        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        self.verify_token_data(token_data)  # 🔥 key part for subclassing
        return token_data

    def verify_token_data(self, token_data: dict):
        # Default does nothing, overridden in subclasses
        pass


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data):
        if token_data and token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Provide a valid access token"
            )
        
class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict):
        if not token_data.get("refresh", False):
            raise HTTPException(status_code=403, detail="Refresh token required")


async def get_current_user(
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    email = token_data["user"]["email"]
    user = await user_service.get_user_by_email(email, session)
    # Handle the case where the user might have been deleted after the token was issued.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found")
    return user

async def ensure_user_is_verified(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address to perform this action"
        )

class RoleChecker:
    def __init__(self, allowed_roles: List[str], detail: str = "You do not have right to perform this action") -> None:
        self.allowed_roles = allowed_roles
        self.detail = detail
        
    async def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role in self.allowed_roles:
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=self.detail
            )