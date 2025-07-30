"""
Mock services for testing dependencies.
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from fastapi import UploadFile
from fastapi_mail import MessageSchema
from io import BytesIO


class MockEmailService:
    """Mock email service for testing."""
    
    def __init__(self):
        self.sent_emails = []
    
    async def send_email(self, background_tasks, message: MessageSchema, template_name: str):
        """Mock email sending."""
        self.sent_emails.append({
            "message": message,
            "template_name": template_name,
            "recipients": message.recipients,
            "subject": message.subject,
            "template_body": message.template_body
        })
        return True
    
    def get_sent_emails(self) -> List[Dict]:
        """Get list of sent emails."""
        return self.sent_emails
    
    def clear_sent_emails(self):
        """Clear sent emails list."""
        self.sent_emails.clear()


class MockStorageService:
    """Mock storage service for testing."""
    
    def __init__(self):
        self.stored_files = {}
        self.file_counter = 0
    
    async def save_file(self, file: UploadFile) -> tuple[str, str, float]:
        """Mock file saving."""
        self.file_counter += 1
        filename = f"mock_file_{self.file_counter}_{file.filename}"
        file_url = f"/static/books/{filename}"
        file_size = 1024.0  # Mock file size
        
        # Store file content for testing
        content = await file.read()
        self.stored_files[file_url] = {
            "filename": filename,
            "content": content,
            "size": file_size,
            "original_filename": file.filename
        }
        
        return filename, file_url, file_size
    
    async def delete_file(self, file_url: str) -> bool:
        """Mock file deletion."""
        if file_url in self.stored_files:
            del self.stored_files[file_url]
            return True
        return False
    
    async def file_exists(self, file_url: str) -> bool:
        """Check if mock file exists."""
        return file_url in self.stored_files
    
    def get_stored_files(self) -> Dict:
        """Get stored files for testing."""
        return self.stored_files
    
    def clear_stored_files(self):
        """Clear stored files."""
        self.stored_files.clear()


class MockDatabaseSession:
    """Mock database session for testing."""
    
    def __init__(self):
        self.data = {}
        self.committed = False
        self.rolled_back = False
    
    async def exec(self, statement):
        """Mock query execution."""
        # Return a mock result
        return MockResult([])
    
    async def commit(self):
        """Mock commit."""
        self.committed = True
    
    async def rollback(self):
        """Mock rollback."""
        self.rolled_back = True
    
    async def refresh(self, instance):
        """Mock refresh."""
        pass
    
    def add(self, instance):
        """Mock add."""
        pass


class MockResult:
    """Mock database result."""
    
    def __init__(self, data: List[Any]):
        self.data = data
    
    def first(self):
        """Return first result."""
        return self.data[0] if self.data else None
    
    def all(self):
        """Return all results."""
        return self.data


class MockUser:
    """Mock user model for testing."""
    
    def __init__(self, uid="test-uid", email="test@example.com", role="user", is_verified=True):
        self.uid = uid
        self.email = email
        self.role = role
        self.is_verified = is_verified
        self.first_name = "Test"
        self.last_name = "User"
        self.password_hash = "$2b$12$mock_hash"
        self.created_at = "2023-01-01T00:00:00"


class MockBook:
    """Mock book model for testing."""
    
    def __init__(self, uid="test-book-uid", title="Test Book", author="Test Author"):
        self.uid = uid
        self.title = title
        self.author = author
        self.description = "Test book description"
        self.file_url = "/static/books/test_book.pdf"
        self.file_size = 1024.0
        self.upload_date = "2023-01-01T00:00:00"
        self.uploaded_by = "test-uid"


class MockBackgroundTasks:
    """Mock background tasks for testing."""
    
    def __init__(self):
        self.tasks = []
    
    def add_task(self, func, *args, **kwargs):
        """Mock adding background task."""
        self.tasks.append({
            "func": func,
            "args": args,
            "kwargs": kwargs
        })
    
    def get_tasks(self):
        """Get added tasks."""
        return self.tasks
    
    def clear_tasks(self):
        """Clear tasks."""
        self.tasks.clear()


def create_mock_upload_file(filename: str = "test.pdf", content: bytes = b"test content") -> UploadFile:
    """Create a mock upload file for testing."""
    file_obj = BytesIO(content)
    return UploadFile(
        filename=filename,
        file=file_obj,
        content_type="application/pdf"
    )


def create_mock_admin_user() -> MockUser:
    """Create a mock admin user."""
    return MockUser(
        uid="admin-uid",
        email="admin@example.com",
        role="admin",
        is_verified=True
    )


def create_mock_superadmin_user() -> MockUser:
    """Create a mock superadmin user."""
    return MockUser(
        uid="superadmin-uid",
        email="superadmin@example.com",
        role="superadmin",
        is_verified=True
    )


# Global mock instances for easy access
mock_email_service = MockEmailService()
mock_storage_service = MockStorageService()
mock_background_tasks = MockBackgroundTasks()


def reset_mocks():
    """Reset all mock services."""
    mock_email_service.clear_sent_emails()
    mock_storage_service.clear_stored_files()
    mock_background_tasks.clear_tasks()
