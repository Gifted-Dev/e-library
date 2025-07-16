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
    token_data: dict = Depends(TokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    email = token_data["user"]["email"]
    user = await user_service.get_user_by_email(email, session)
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles
        
    async def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role in self.allowed_roles:
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Restricted!"
            )