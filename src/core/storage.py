import os
import io
import uuid
from pathlib import Path
from urllib.parse import urlparse
import asyncio
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from src.config import Config
import aiofiles
import aioboto3
from botocore.exceptions import ClientError

# Define a base directory for static files. This makes path resolution robust.
BASE_STATIC_DIR = Path(__file__).parent.parent / "static"

class LocalStorageService:
    async def save_file(self, file: UploadFile, folder="books"):
        # Ensure the save directory exists within our base static directory.
        save_dir = BASE_STATIC_DIR / folder
        save_dir.mkdir(parents=True, exist_ok=True)

        file_id = str(uuid.uuid4())
        unique_filename = f"{file_id}_{file.filename}"
        full_path = save_dir / unique_filename

        # Save the file
        content = await file.read()
        file_size = len(content) / (1024 * 1024)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        # Return the original filename for display, and a portable, URL-like relative path for storage.
        relative_path = f"/{folder}/{unique_filename}".replace("\\", "/")
        return file.filename, relative_path, file_size

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolves a relative URL path to an absolute filesystem path."""
        # Remove leading slash and safely join with the base static directory.
        return BASE_STATIC_DIR / relative_path.lstrip('/')

    async def file_exists(self, relative_path: str) -> bool:
        full_path = self._resolve_path(relative_path)
        return os.path.exists(full_path)
    
    async def delete_file(self, relative_path: str):
        full_path = self._resolve_path(relative_path)
        try:
            # Use a thread pool for the blocking I/O call to avoid stalling the event loop.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, os.remove, full_path)
        except FileNotFoundError:
            # If the file is already gone, we can safely ignore the error.
            pass

    async def get_download_response(self, relative_path: str):
        full_path = self._resolve_path(relative_path)
        # Extract the original filename part for the download header.
        original_filename = "_".join(full_path.name.split('_')[1:])
        return FileResponse(path=full_path, filename=original_filename)



class S3StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket_name = Config.AWS_BUCKET_NAME
        self.s3_config = {
            "aws_access_key_id": Config.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": Config.AWS_SECRET_ACCESS_KEY,
            "region_name": Config.AWS_REGION
        }

    async def save_file(self, file: UploadFile, folder="books"):
        async with self.session.client("s3", **self.s3_config) as s3:
            file_id = str(uuid.uuid4())
            key = f"{folder}/{file_id}_{file.filename}"
            content = await file.read()
            file_size = len(content) / (1024 * 1024)

            await s3.put_object(
                Body=content,
                Bucket=Config.AWS_BUCKET_NAME,
                Key=key,
                ContentType=file.content_type
            )

            file_url = f"https://{Config.AWS_BUCKET_NAME}.s3.amazonaws.com/{key}"
            # Return the original filename for display, and the full S3 URL for storage.
            return file.filename, file_url, file_size

    async def file_exists(self, file_url: str) -> bool:
        # Reliably extract the object key (e.g., "books/file.pdf") from the full URL.
        parsed_url = urlparse(file_url)
        key = parsed_url.path.lstrip('/')

        async with self.session.client("s3", **self.s3_config) as s3:
            try:
                # head_object is a lightweight way to check for existence.
                await s3.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except ClientError as e:
                # If the specific error code is 404, we know the file doesn't exist.
                if e.response['Error']['Code'] == '404':
                    return False
                # For any other client error (e.g., permissions), we re-raise the exception.
                raise
            
    async def delete_file(self, file_url: str):
        # Reliably extract the object key (e.g., "books/file.pdf") from the full URL.
        parsed_url = urlparse(file_url)
        key = parsed_url.path.lstrip('/')
        
        async with self.session.client("s3", **self.s3_config) as s3:
            
            await s3.delete_object(Bucket=self.bucket_name, Key=key)
            
    async def get_download_response(self, file_url: str):
        """Generates a pre-signed URL for S3 and returns a RedirectResponse."""
        parsed_url = urlparse(file_url)
        key = parsed_url.path.lstrip('/')

        async with self.session.client("s3", **self.s3_config) as s3:
            try:
                presigned_url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=300  # URL is valid for 5 minutes
                )
                return RedirectResponse(url=presigned_url)
            except ClientError:
                raise HTTPException(status_code=500, detail="Could not generate download link.")


# 👇 Choose the right storage handler dynamically
def get_storage_service():
    if Config.STORAGE_BACKEND == "s3":
        return S3StorageService()
    return LocalStorageService()
