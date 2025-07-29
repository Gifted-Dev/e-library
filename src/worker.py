import asyncio
from celery import Celery
from typing import Optional, Dict, Any, List
from src.config import Config
from src.core.email import send_email, create_template_message
from src.core.storage import get_storage_service

celery_app = Celery(
    "worker",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL
)

@celery_app.task
def delete_book_file_from_storage_task(file_url: Optional[str]) -> None:
    
    """
    A Celery task to delete a file from storage.
    Celery tasks are synchronous, but our storage code is async.
    We use asyncio.run() to bridge the gap.
    """
    
    async def _delete():
        if not file_url:
            return
        storage_service = get_storage_service()
        
        if await storage_service.file_exists(file_url):
            await storage_service.delete_file(file_url)
            
    asyncio.run(_delete())
    
@celery_app.task(name="send_email")
def send_email_task(subject: str, recipients: List[str], template_body: Dict[str, Any], template_name: str) -> None:
    """
    Creates a message object from a dictionary and sends the email.
    This task runs within a Celery worker, not the main FastAPI process.
    """
    message = create_template_message(
        subject=subject,
        recipients=recipients,
        template_body=template_body
    )
    
    # Since send_email is an async function, we must run it in an event loop.
    asyncio.run(send_email(message, template_name=template_name))