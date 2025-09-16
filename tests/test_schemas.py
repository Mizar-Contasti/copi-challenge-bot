"""
Unit tests for Pydantic schemas validation.
Tests strict validation requirements and error handling.
"""

import pytest
from pydantic import ValidationError
from app.models.schemas import ChatRequest, ChatResponse, MessageSchema, ErrorResponse, HealthResponse


class TestChatRequest:
    """Test ChatRequest schema validation."""
    
    def test_valid_request_with_conversation_id(self):
        """Test valid request with conversation_id."""
        request = ChatRequest(
            conversation_id="test-123",
            message="Hello world"
        )
        assert request.conversation_id == "test-123"
        assert request.message == "Hello world"
    
    def test_valid_request_without_conversation_id(self):
        """Test valid request without conversation_id."""
        request = ChatRequest(
            conversation_id=None,
            message="Hello world"
        )
        assert request.conversation_id is None
        assert request.message == "Hello world"
    
    def test_empty_conversation_id_becomes_none(self):
        """Test that empty string conversation_id becomes None."""
        request = ChatRequest(
            conversation_id="",
            message="Hello world"
        )
        assert request.conversation_id is None
    
    def test_message_required(self):
        """Test that message is required."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(conversation_id="test")
        
        errors = exc_info.value.errors()
        assert any(error['type'] == 'missing' for error in errors)
    
    def test_empty_message_rejected(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(
                conversation_id="test",
                message=""
            )
    
    def test_message_too_long_rejected(self):
        """Test that messages exceeding max length are rejected."""
        long_message = "a" * 6000  # Exceeds 5000 char limit
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                conversation_id="test",
                message=long_message
            )
        
        errors = exc_info.value.errors()
        assert any("exceeds maximum length" in str(error) for error in errors)
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                conversation_id="test",
                message="hello",
                extra_field="not allowed"
            )
        
        errors = exc_info.value.errors()
        assert any(error['type'] == 'extra_forbidden' for error in errors)
    
    def test_message_whitespace_stripped(self):
        """Test that message whitespace is stripped."""
        request = ChatRequest(
            conversation_id="test",
            message="  hello world  "
        )
        assert request.message == "hello world"


class TestMessageSchema:
    """Test MessageSchema validation."""
    
    def test_valid_message(self):
        """Test valid message schema."""
        message = MessageSchema(
            turn=1,
            role="user",
            message="Hello"
        )
        assert message.turn == 1
        assert message.role == "user"
        assert message.message == "Hello"
    
    def test_invalid_role_rejected(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MessageSchema(
                turn=1,
                role="invalid",
                message="Hello"
            )
        
        errors = exc_info.value.errors()
        assert any("Role must be 'user' or 'bot'" in str(error) for error in errors)


class TestChatResponse:
    """Test ChatResponse schema validation."""
    
    def test_valid_response(self):
        """Test valid chat response."""
        response = ChatResponse(
            conversation_id="test-123",
            messages=[
                MessageSchema(turn=1, role="user", message="Hello"),
                MessageSchema(turn=1, role="bot", message="Hi there")
            ],
            conversation_history=[
                MessageSchema(turn=1, role="user", message="Hello"),
                MessageSchema(turn=1, role="bot", message="Hi there")
            ]
        )
        assert response.conversation_id == "test-123"
        assert len(response.messages) == 2
        assert len(response.conversation_history) == 2


class TestErrorResponse:
    """Test ErrorResponse schema validation."""
    
    def test_valid_error_response(self):
        """Test valid error response."""
        error = ErrorResponse(
            error="Test Error",
            message="Test message",
            postman_collection="http://example.com/postman",
            swagger_docs="http://example.com/docs"
        )
        assert error.error == "Test Error"
        assert error.message == "Test message"
        assert error.postman_collection == "http://example.com/postman"
        assert error.swagger_docs == "http://example.com/docs"


class TestHealthResponse:
    """Test HealthResponse schema validation."""
    
    def test_valid_health_response(self):
        """Test valid health response."""
        health = HealthResponse(
            status="healthy",
            timestamp="2024-01-01T00:00:00Z",
            version="1.0.0"
        )
        assert health.status == "healthy"
        assert health.timestamp == "2024-01-01T00:00:00Z"
        assert health.version == "1.0.0"
