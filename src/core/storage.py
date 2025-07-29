import os
import io
import uuid
from urllib.parse import urlparse
import asyncio
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from src.config import Config
import aiofiles
import aioboto3
from botocore.exceptions import ClientError


class LocalStorageService:
    async def save_file(self, file: UploadFile, folder="src/static/books"):
        os.makedirs(folder, exist_ok=True)
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        path = os.path.join(folder, filename)

        # Save the file
        
        content = await file.read()
        file_size = len(content) / (1024 * 1024)

        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

        return filename, path, file_size

    async def file_exists(self, file_path: str) -> bool:
        # This is a robust way to check for file existence asynchronously
        # without relying on aiofiles.os, which can cause issues in some environments.
        try:
            async with aiofiles.open(file_path, mode="r"):
                pass
            return True
        except FileNotFoundError:
            return False
    
    async def delete_file(self, file_url: str):
        # To avoid the 'aiofiles has no attribute os' error, we can run the
        # blocking os.remove call in a separate thread using asyncio's executor.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, os.remove, file_url)
        
    async def get_download_response(self, file_path: str):
        """Returns a FileResponse for a local file."""
        original_filename = os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type='application/octet-stream'
        )



class S3StorageService:
    async def save_file(self, file: UploadFile, folder="books"):
        session = aioboto3.Session()
        
        
        async with session.client(
            "s3",
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        ) as s3:

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
            return key, file_url, file_size

    async def file_exists(self, file_url: str) -> bool:
        session = aioboto3.Session()
        bucket_name = Config.AWS_BUCKET_NAME
        
        # Reliably extract the object key (e.g., "books/file.pdf") from the full URL.
        parsed_url = urlparse(file_url)
        key = parsed_url.path.lstrip('/')

        async with session.client("s3",
                                  aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                                  region_name=Config.AWS_REGION) as s3:
            try:
                # head_object is a lightweight way to check for existence.
                await s3.head_object(Bucket=bucket_name, Key=key)
                return True
            except ClientError as e:
                # If the specific error code is 404, we know the file doesn't exist.
                if e.response['Error']['Code'] == '404':
                    return False
                # For any other client error (e.g., permissions), we re-raise the exception.
                raise
            
    async def delete_file(self, file_url: str):
        session = aioboto3.Session()
        bucket_name = Config.AWS_BUCKET_NAME
        
        # Reliably extract the object key (e.g., "books/file.pdf") from the full URL.
        parsed_url = urlparse(file_url)
        key = parsed_url.path.lstrip('/')
        
        
        
        async with session.client("s3",
                                  aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                                  region_name=Config.AWS_REGION) as s3:
            
            await s3.delete_object(Bucket=bucket_name, Key=key)
            
    async def get_download_response(self, file_url: str):
        """Generates a pre-signed URL for S3 and returns a RedirectResponse."""
        session = aioboto3.Session()
        bucket_name = Config.AWS_BUCKET_NAME
        parsed_url = urlparse(file_url)
        key = parsed_url.path.lstrip('/')

        async with session.client("s3",
                                  aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                                  region_name=Config.AWS_REGION) as s3:
            try:
                presigned_url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': key},
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
