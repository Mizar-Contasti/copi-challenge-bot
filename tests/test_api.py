"""
Unit tests for FastAPI endpoints.
Tests API functionality, validation, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.schemas import ChatRequest, ChatResponse


client = TestClient(app)


class TestChatEndpoint:
    """Test /chat endpoint functionality."""
    
    @patch('app.services.conversation_service.start_new_conversation')
    def test_new_conversation_success(self, mock_start):
        """Test successful new conversation creation."""
        mock_start.return_value = {
            "conversation_id": "test-123",
            "messages": [
                {"turn": 1, "role": "user", "message": "Hello"},
                {"turn": 1, "role": "bot", "message": "Hi there"}
            ],
            "conversation_history": [
                {"turn": 1, "role": "user", "message": "Hello"},
                {"turn": 1, "role": "bot", "message": "Hi there"}
            ]
        }
        
        response = client.post("/chat", json={
            "conversation_id": None,
            "message": "Hello"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-123"
        assert len(data["messages"]) == 2
        assert len(data["conversation_history"]) == 2
    
    @patch('app.services.conversation_service.continue_conversation')
    def test_continue_conversation_success(self, mock_continue):
        """Test successful conversation continuation."""
        mock_continue.return_value = {
            "conversation_id": "test-123",
            "messages": [
                {"turn": 2, "role": "user", "message": "How are you?"},
                {"turn": 2, "role": "bot", "message": "I'm doing well"}
            ],
            "conversation_history": [
                {"turn": 1, "role": "user", "message": "Hello"},
                {"turn": 1, "role": "bot", "message": "Hi there"},
                {"turn": 2, "role": "user", "message": "How are you?"},
                {"turn": 2, "role": "bot", "message": "I'm doing well"}
            ]
        }
        
        response = client.post("/chat", json={
            "conversation_id": "test-123",
            "message": "How are you?"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-123"
        assert len(data["messages"]) == 2
        assert len(data["conversation_history"]) == 4
    
    def test_missing_message_field(self):
        """Test request with missing message field."""
        response = client.post("/chat", json={
            "conversation_id": "test-123"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_empty_message_rejected(self):
        """Test request with empty message."""
        response = client.post("/chat", json={
            "conversation_id": "test-123",
            "message": ""
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_extra_fields_rejected(self):
        """Test request with extra fields."""
        response = client.post("/chat", json={
            "conversation_id": "test-123",
            "message": "Hello",
            "extra_field": "not allowed"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Invalid request format"
        assert "Only 'conversation_id' and 'message' attributes are allowed" in data["message"]
    
    def test_message_too_long_rejected(self):
        """Test request with message exceeding length limit."""
        long_message = "a" * 6000
        response = client.post("/chat", json={
            "conversation_id": "test-123",
            "message": long_message
        })
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.conversation_service.continue_conversation')
    def test_conversation_not_found(self, mock_continue):
        """Test conversation not found error."""
        from app.middleware import ConversationNotFoundError
        mock_continue.side_effect = ConversationNotFoundError("Conversation not found")
        
        response = client.post("/chat", json={
            "conversation_id": "nonexistent",
            "message": "Hello"
        })
        
        assert response.status_code == 404
    
    @patch('app.services.conversation_service.start_new_conversation')
    def test_ai_service_error(self, mock_start):
        """Test AI service error handling."""
        from app.middleware import AIServiceError
        mock_start.side_effect = AIServiceError("AI service failed")
        
        response = client.post("/chat", json={
            "conversation_id": None,
            "message": "Hello"
        })
        
        assert response.status_code == 503


class TestHealthEndpoint:
    """Test /health endpoint functionality."""
    
    def test_health_check_success(self):
        """Test successful health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestRootEndpoint:
    """Test root endpoint functionality."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @patch('app.services.conversation_service.start_new_conversation')
    def test_rate_limit_exceeded(self, mock_start):
        """Test rate limiting with many requests."""
        mock_start.return_value = {
            "conversation_id": "test-123",
            "messages": [],
            "conversation_history": []
        }
        
        # Make many requests quickly
        responses = []
        for i in range(105):  # Exceed 100 per minute limit
            response = client.post("/chat", json={
                "conversation_id": None,
                "message": f"Hello {i}"
            })
            responses.append(response)
        
        # Some requests should be rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0
        
        # Check rate limit response format
        if rate_limited:
            data = rate_limited[0].json()
            assert data["error"] == "Rate limit exceeded"
            assert "retry_after" in data


class TestSwaggerDocs:
    """Test Swagger documentation endpoints."""
    
    def test_swagger_docs_accessible(self):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json_accessible(self):
        """Test that OpenAPI JSON is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
