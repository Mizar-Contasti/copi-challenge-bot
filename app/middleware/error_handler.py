"""
Global error handling middleware for the debate bot API.
Handles exceptions and provides consistent error responses.
"""

import traceback
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling and consistent error responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive error handling."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTP exceptions (already handled)
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "HTTP Exception",
                    "message": e.detail,
                    "postman_collection": settings.postman_collection_url,
                    "swagger_docs": settings.swagger_docs_url
                }
            )
            
        except RequestValidationError as e:
            # Pydantic validation errors
            logger.warning(f"Validation error: {e}")
            return self._handle_validation_error(e)
            
        except ValidationError as e:
            # Additional Pydantic validation errors
            logger.warning(f"Pydantic validation error: {e}")
            return self._handle_validation_error(e)
            
        except ValueError as e:
            # Value errors (e.g., invalid conversation_id)
            logger.warning(f"Value error: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid input",
                    "message": str(e),
                    "postman_collection": settings.postman_collection_url,
                    "swagger_docs": settings.swagger_docs_url
                }
            )
            
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Don't expose internal errors in production
            if settings.environment == "production":
                error_message = "An internal error occurred"
            else:
                error_message = str(e)
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": error_message,
                    "postman_collection": settings.postman_collection_url,
                    "swagger_docs": settings.swagger_docs_url
                }
            )
    
    def _handle_validation_error(self, error: Union[RequestValidationError, ValidationError]) -> JSONResponse:
        """Handle Pydantic validation errors with detailed messages."""
        
        # Check if this is the "extra attributes" error we want to catch
        error_details = []
        has_extra_fields = False
        
        if hasattr(error, 'errors'):
            for err in error.errors():
                error_type = err.get('type', '')
                field = err.get('loc', ['unknown'])[-1]
                
                if error_type == 'extra_forbidden':
                    has_extra_fields = True
                    error_details.append(f"Extra field '{field}' not allowed")
                else:
                    error_details.append(f"{field}: {err.get('msg', 'Invalid value')}")
        
        # Special handling for extra fields (our strict validation requirement)
        if has_extra_fields:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid request format",
                    "message": "Only 'conversation_id' and 'message' attributes are allowed",
                    "postman_collection": settings.postman_collection_url,
                    "swagger_docs": settings.swagger_docs_url
                }
            )
        
        # General validation error
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation error",
                "message": "; ".join(error_details) if error_details else "Invalid input format",
                "postman_collection": settings.postman_collection_url,
                "swagger_docs": settings.swagger_docs_url
            }
        )


# Custom exception classes
class ConversationNotFoundError(Exception):
    """Raised when a conversation is not found."""
    pass


class AIServiceError(Exception):
    """Raised when AI service fails."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass
