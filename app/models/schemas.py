"""
Pydantic schemas for request/response validation and serialization.
Implements strict validation according to the work-plan requirements.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from app.config import settings


class ChatRequest(BaseModel):
    """
    Chat request schema with strict validation.
    Only allows conversation_id and message attributes.
    """
    conversation_id: Optional[str] = Field(None, description="Conversation ID (can be null, empty string, or valid string)")
    message: str = Field(..., min_length=1, description="User message (required, non-empty)")
    
    @field_validator('message')
    @classmethod
    def validate_message_length(cls, v):
        """Validate message length doesn't exceed maximum."""
        if len(v) > settings.max_message_length:
            raise ValueError(f"Message exceeds maximum length of {settings.max_message_length} characters")
        return v.strip()
    
    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v):
        """Normalize conversation_id (treat empty string as None)."""
        if v == "" or v == "null":
            return None
        return v
    
    class Config:
        # Forbid extra attributes - only conversation_id and message allowed
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "conversation_id": "abc123-def456-ghi789",
                "message": "I think climate change is caused by humans"
            }
        }


class MessageSchema(BaseModel):
    """Schema for individual messages in responses."""
    turn: int = Field(..., description="Turn number")
    role: str = Field(..., description="Message role (user or bot)")
    message: str = Field(..., description="Message content")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is either 'user' or 'bot'."""
        if v not in ['user', 'bot']:
            raise ValueError("Role must be 'user' or 'bot'")
        return v


class ChatResponse(BaseModel):
    """
    Chat response schema with current turn messages and full conversation history.
    """
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[MessageSchema] = Field(..., description="Current turn messages (user + bot)")
    conversation_history: List[MessageSchema] = Field(..., description="All messages ordered by turn")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "abc123-def456-ghi789",
                "messages": [
                    {
                        "turn": 2,
                        "role": "user",
                        "message": "But what about the scientific evidence?"
                    },
                    {
                        "turn": 2,
                        "role": "bot",
                        "message": "The so-called 'evidence' is manipulated by institutions with vested interests..."
                    }
                ],
                "conversation_history": [
                    {
                        "turn": 1,
                        "role": "user",
                        "message": "I think climate change is caused by humans"
                    },
                    {
                        "turn": 1,
                        "role": "bot",
                        "message": "That's a common misconception. Climate change is actually a natural phenomenon..."
                    },
                    {
                        "turn": 2,
                        "role": "user",
                        "message": "But what about the scientific evidence?"
                    },
                    {
                        "turn": 2,
                        "role": "bot",
                        "message": "The so-called 'evidence' is manipulated by institutions with vested interests..."
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema for validation and other errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    postman_collection: Optional[str] = Field(None, description="URL to Postman collection")
    swagger_docs: str = Field(..., description="URL to Swagger documentation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid request format",
                "message": "Only 'conversation_id' and 'message' attributes are allowed",
                "postman_collection": "[PLACEHOLDER_POSTMAN_URL]",
                "swagger_docs": "https://api.example.com/docs"
            }
        }


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0"
            }
        }