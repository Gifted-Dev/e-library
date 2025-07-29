import asyncio
from celery import Celery
from typing import Optional, Dict, Any
from src.config import Config
from src.core.email import send_email, create_template_message
from src.core.storage import get_storage_service

celery_app = Celery(
    "worker",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL
)

# Celery 5+ has native support for async tasks.
# By defining the task function with `async def`, Celery's event loop
# will run it correctly without needing `asyncio.run()`.

@celery_app.task
async def delete_book_file_from_storage_task(file_url: Optional[str]) -> None:
    """
    A Celery task to delete a file from storage.
    This is an async task, allowing efficient I/O operations.
    """
    if not file_url:
        return
    storage_service = get_storage_service()
    if await storage_service.file_exists(file_url):
        await storage_service.delete_file(file_url)
    
@celery_app.task(name="send_email")
async def send_email_task(message_data: Dict[str, Any], template_name: str) -> None:
    """
    Creates a message object from a dictionary and sends the email asynchronously.
    This task runs within a Celery worker, not the main FastAPI process.
    """
    message = create_template_message(**message_data)
    await send_email(message, template_name=template_name)