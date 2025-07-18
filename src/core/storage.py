import os
import io
import uuid
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")


class LocalStorageService:
    async def save_file(self, file: UploadFile, folder="src/static/books"):
        os.makedirs(folder, exist_ok=True)
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        path = os.path.join(folder, filename)

        # Save the file
        
        content = await file.read()
        file_size = len(content) / (1024 * 1024)

        with open(path, "wb") as f:
            f.write(content)

        return filename, path, file_size


class S3StorageService:
    async def save_file(self, file: UploadFile, folder="books"):
        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )

        file_id = str(uuid.uuid4())
        key = f"{folder}/{file_id}_{file.filename}"
        content = await file.read()
        file_size = len(content) / (1024 * 1024)


        s3.upload_fileobj(io.BytesIO(content), os.getenv("AWS_BUCKET_NAME"), key)

        file_url = f"https://{os.getenv('AWS_BUCKET_NAME')}.s3.amazonaws.com/{key}"
        return key, file_url, file_size


# 👇 Choose the right storage handler dynamically
def get_storage_service():
    if STORAGE_BACKEND == "s3":
        return S3StorageService()
    return LocalStorageService()
