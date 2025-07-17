from fastapi import APIRouter, status, Depends, UploadFile, File
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.auth.dependencies import AccessTokenBearer, RoleChecker

book_router = APIRouter()
role_checker = RoleChecker(['admin, user'])
admin_checker = RoleChecker(['admin'])

# @book_router.post("/upload")
# async def upload_file( ):


