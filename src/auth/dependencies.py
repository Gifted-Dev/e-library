from fastapi.security import HTTPBearer
from fastapi import Request, Depends, status
from fastapi.exceptions import HTTPException
from src.auth.utils import decode_token
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.auth.services import UserService
from src.db.models import User
from src.core.redis import get_redis_service, RedisService
from typing import List, Optional


user_service = UserService()

async def cookie_or_header_bearer(request: Request) -> Optional[str]:
    """
    Dependency to extract JWT token from either the 'access_token' cookie
    or the 'Authorization: Bearer' header. Cookie is checked first.
    """
    token = request.cookies.get("access_token")
    if token:
        # The token in the cookie is stored as "Bearer <token>"
        if token.startswith("Bearer "):
            return token.split(" ")[1]
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    
    return None

class TokenBearer(HTTPBearer):
    async def __call__(self, request: Request) -> dict:
        credentials = await super().__call__(request)
        token = credentials.credentials
        token_data = decode_token(token)

        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Check if token is in blocklist
        redis_service = await get_redis_service()
        if await redis_service.is_connected():
            jti = token_data.get("jti")
            if jti and await redis_service.is_token_blocked(jti):
                raise HTTPException(status_code=401, detail="Token has been revoked")

        self.verify_token_data(token_data)  # 🔥 key part for subclassing
        return token_data

    def verify_token_data(self, token_data: dict):
        # Default does nothing, overridden in subclasses
        pass

async def get_validated_token_data(token: Optional[str] = Depends(cookie_or_header_bearer)) -> Optional[dict]:
    """
    Decodes and validates a token, checking for blocklist and token type.
    This replaces the old AccessTokenBearer class.
    """
    if not token:
        return None

    token_data = decode_token(token)

    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Check if token is in blocklist
    redis_service = await get_redis_service()
    if await redis_service.is_connected():
        jti = token_data.get("jti")
        if jti and await redis_service.is_token_blocked(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")

    # Verify it's an access token, not a refresh token
    if token_data.get('refresh'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provide a valid access token"
        )
    
    return token_data

# This class is still needed for the /refresh endpoint
class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict):
        if not token_data.get("refresh", False):
            raise HTTPException(status_code=403, detail="Refresh token required")


async def get_current_user(
    token_data: Optional[dict] = Depends(get_validated_token_data),
    session: AsyncSession = Depends(get_session)
) -> User:
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

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

async def get_current_user_or_none(
    token_data: Optional[dict] = Depends(get_validated_token_data),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """
    A dependency that fetches the current user if a valid token is provided,
    but returns None instead of raising an error if the user is not authenticated.
    Ideal for pages that have both public and authenticated states.
    """
    if not token_data:
        return None
    
    try:
        email = token_data["user"]["email"]
        user = await user_service.get_user_by_email(email, session)
        return user
    except Exception:
        return None

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