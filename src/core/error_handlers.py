"""
Error handlers for the e-library application.
"""

import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
from src.core.exceptions import ELibraryException
import traceback
from typing import Union

# Configure logging
logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    message: str,
    details: dict = None,
    error_type: str = "error"
) -> JSONResponse:
    """Create a standardized error response."""
    content = {
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def elibrary_exception_handler(request: Request, exc: ELibraryException) -> JSONResponse:
    """Handle custom e-library exceptions."""
    logger.warning(f"ELibraryException: {exc.message} - {exc.details}")
    
    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
        error_type=exc.__class__.__name__
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_type="HTTPException"
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(f"ValidationError: {exc.errors()}")
    
    # Format validation errors for better readability
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        details={"validation_errors": formatted_errors},
        error_type="ValidationError"
    )


async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(f"PydanticValidationError: {exc.errors()}")
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Data validation failed",
        details={"validation_errors": exc.errors()},
        error_type="PydanticValidationError"
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(f"SQLAlchemyError: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Don't expose internal database errors to users
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="A database error occurred. Please try again later.",
        error_type="DatabaseError"
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Don't expose internal errors to users in production
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        error_type="InternalServerError"
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions (e.g., invalid UUID format)."""
    logger.warning(f"ValueError: {str(exc)}")
    
    # Check if it's a UUID error
    if "UUID" in str(exc) or "hexadecimal" in str(exc):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid ID format provided",
            error_type="InvalidFormatError"
        )
    
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid value provided",
        details={"original_error": str(exc)},
        error_type="ValueError"
    )


async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Handle KeyError exceptions."""
    logger.warning(f"KeyError: {str(exc)}")
    
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message=f"Missing required field: {str(exc)}",
        error_type="MissingFieldError"
    )


async def type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
    """Handle TypeError exceptions."""
    logger.warning(f"TypeError: {str(exc)}")
    
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid data type provided",
        details={"original_error": str(exc)},
        error_type="TypeError"
    )


# Dictionary mapping exception types to their handlers
EXCEPTION_HANDLERS = {
    ELibraryException: elibrary_exception_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    PydanticValidationError: pydantic_validation_exception_handler,
    SQLAlchemyError: sqlalchemy_exception_handler,
    ValueError: value_error_handler,
    KeyError: key_error_handler,
    TypeError: type_error_handler,
    Exception: general_exception_handler,  # Catch-all for unexpected errors
}
