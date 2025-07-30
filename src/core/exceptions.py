"""
Custom exception classes for the e-library application.
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class ELibraryException(Exception):
    """Base exception class for e-library application."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ELibraryException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class AuthenticationError(ELibraryException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class AuthorizationError(ELibraryException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class NotFoundError(ELibraryException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class ConflictError(ELibraryException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


class BusinessLogicError(ELibraryException):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str = "Business logic error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class ExternalServiceError(ELibraryException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, details)


class FileProcessingError(ELibraryException):
    """Raised when file processing fails."""
    
    def __init__(self, message: str = "File processing error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class DatabaseError(ELibraryException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


# User-specific exceptions
class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""
    
    def __init__(self, user_identifier: str = ""):
        message = f"User not found: {user_identifier}" if user_identifier else "User not found"
        super().__init__(message)


class UserAlreadyExistsError(ConflictError):
    """Raised when trying to create a user that already exists."""
    
    def __init__(self, email: str = ""):
        message = f"User with email {email} already exists" if email else "User already exists"
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class UserNotVerifiedError(AuthorizationError):
    """Raised when user is not verified."""
    
    def __init__(self, message: str = "Please verify your email address to perform this action"):
        super().__init__(message)


# Book-specific exceptions
class BookNotFoundError(NotFoundError):
    """Raised when a book is not found."""
    
    def __init__(self, book_identifier: str = ""):
        message = f"Book not found: {book_identifier}" if book_identifier else "Book not found"
        super().__init__(message)


class BookAlreadyExistsError(ConflictError):
    """Raised when trying to create a book that already exists."""
    
    def __init__(self, title: str = "", author: str = ""):
        if title and author:
            message = f"Book '{title}' by {author} already exists"
        else:
            message = "Book already exists"
        super().__init__(message)


class InvalidFileTypeError(ValidationError):
    """Raised when an invalid file type is uploaded."""
    
    def __init__(self, allowed_types: list = None):
        if allowed_types:
            message = f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        else:
            message = "Invalid file type"
        super().__init__(message)


# Token-specific exceptions
class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""
    
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


# Role-specific exceptions
class InsufficientPermissionsError(AuthorizationError):
    """Raised when user doesn't have required permissions."""
    
    def __init__(self, required_role: str = "", current_role: str = ""):
        if required_role and current_role:
            message = f"Insufficient permissions. Required: {required_role}, Current: {current_role}"
        else:
            message = "Insufficient permissions for this action"
        super().__init__(message)
