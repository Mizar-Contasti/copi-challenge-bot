"""
Unit tests for service layer functionality.
Tests conversation service and retry service.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.conversation_service import ConversationService
from app.services.retry_service import OpenAIClientManager
from app.middleware import ConversationNotFoundError, AIServiceError


class TestConversationService:
    """Test ConversationService functionality."""
    
    @pytest.fixture
    def service(self):
        """Create ConversationService instance for testing."""
        return ConversationService()
    
    @patch('app.services.conversation_service.db_manager')
    @patch('app.services.conversation_service.topic_analysis_chain')
    @patch('app.services.conversation_service.position_assignment_chain')
    @patch('app.services.conversation_service.persuasive_response_chain')
    @patch('app.services.conversation_service.consistency_validation_chain')
    def test_start_new_conversation_success(self, mock_validation, mock_response, 
                                          mock_position, mock_topic, mock_db, service):
        """Test successful new conversation creation."""
        # Mock chain responses
        mock_topic.analyze_topic.return_value = {
            "topic": "Climate Change",
            "category": "Climate Change",
            "description": "Climate debate"
        }
        mock_position.assign_position.return_value = "Climate change is natural"
        mock_response.generate_response.return_value = "I believe climate change is primarily natural."
        mock_validation.validate_response.return_value = {
            "is_consistent": True,
            "is_persuasive": True,
            "is_appropriate": True,
            "overall_score": 8
        }
        
        # Mock database operations
        mock_db.create_conversation.return_value = "test-123"
        mock_db.add_message.return_value = True
        mock_db.get_current_turn_messages.return_value = [
            {"turn": 1, "role": "user", "message": "Hello"},
            {"turn": 1, "role": "bot", "message": "I believe climate change is primarily natural."}
        ]
        mock_db.get_conversation_history.return_value = [
            {"turn": 1, "role": "user", "message": "Hello"},
            {"turn": 1, "role": "bot", "message": "I believe climate change is primarily natural."}
        ]
        
        result = service.start_new_conversation("Hello")
        
        assert result["conversation_id"] == "test-123"
        assert len(result["messages"]) == 2
        assert len(result["conversation_history"]) == 2
    
    @patch('app.services.conversation_service.db_manager')
    def test_continue_conversation_not_found(self, mock_db, service):
        """Test continuing non-existent conversation."""
        mock_db.get_conversation.return_value = None
        
        with pytest.raises(ConversationNotFoundError):
            service.continue_conversation("nonexistent", "Hello")
    
    @patch('app.services.conversation_service.db_manager')
    @patch('app.services.conversation_service.persuasive_response_chain')
    @patch('app.services.conversation_service.consistency_validation_chain')
    def test_continue_conversation_success(self, mock_validation, mock_response, mock_db, service):
        """Test successful conversation continuation."""
        # Mock existing conversation
        mock_db.get_conversation.return_value = {
            "id": "test-123",
            "topic": "Climate Change",
            "bot_position": "Climate change is natural"
        }
        mock_db.get_next_turn.return_value = 2
        mock_db.get_conversation_history.return_value = [
            {"turn": 1, "role": "user", "message": "Hello"},
            {"turn": 1, "role": "bot", "message": "Hi there"}
        ]
        
        # Mock response generation
        mock_response.generate_response.return_value = "Natural cycles explain climate variations."
        mock_validation.validate_response.return_value = {
            "is_consistent": True,
            "is_persuasive": True,
            "is_appropriate": True,
            "overall_score": 8
        }
        
        # Mock database operations
        mock_db.add_message.return_value = True
        mock_db.get_current_turn_messages.return_value = [
            {"turn": 2, "role": "user", "message": "Tell me more"},
            {"turn": 2, "role": "bot", "message": "Natural cycles explain climate variations."}
        ]
        mock_db.get_conversation_history.return_value = [
            {"turn": 1, "role": "user", "message": "Hello"},
            {"turn": 1, "role": "bot", "message": "Hi there"},
            {"turn": 2, "role": "user", "message": "Tell me more"},
            {"turn": 2, "role": "bot", "message": "Natural cycles explain climate variations."}
        ]
        
        result = service.continue_conversation("test-123", "Tell me more")
        
        assert result["conversation_id"] == "test-123"
        assert len(result["messages"]) == 2
        assert len(result["conversation_history"]) == 4
    
    @patch('app.services.conversation_service.db_manager')
    @patch('app.services.conversation_service.topic_analysis_chain')
    def test_start_conversation_chain_error(self, mock_topic, mock_db, service):
        """Test handling of chain errors during conversation start."""
        mock_topic.analyze_topic.side_effect = Exception("Chain error")
        
        with pytest.raises(AIServiceError):
            service.start_new_conversation("Hello")


class TestOpenAIClientManager:
    """Test OpenAIClientManager functionality."""
    
    @pytest.fixture
    def client_manager(self):
        """Create OpenAIClientManager instance for testing."""
        return OpenAIClientManager()
    
    @patch('app.services.retry_service.openai.OpenAI')
    def test_safe_call_success(self, mock_openai_class, client_manager):
        """Test successful API call with retry logic."""
        # Mock successful response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        def mock_create(**kwargs):
            return mock_response
        
        mock_client.chat.completions.create = mock_create
        
        # Test safe call
        result = client_manager.safe_call(
            mock_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert result == mock_response
    
    @patch('app.services.retry_service.openai.OpenAI')
    def test_safe_call_retry_on_rate_limit(self, mock_openai_class, client_manager):
        """Test retry logic on rate limit errors."""
        import openai
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock rate limit error then success
        call_count = 0
        def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise openai.RateLimitError("Rate limit exceeded", response=None, body=None)
            else:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = "Success"
                return mock_response
        
        mock_client.chat.completions.create = mock_create
        
        # Should succeed after retry
        result = client_manager.safe_call(
            mock_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert call_count == 2  # One failure, one success
    
    @patch('app.services.retry_service.openai.OpenAI')
    def test_safe_call_max_retries_exceeded(self, mock_openai_class, client_manager):
        """Test behavior when max retries are exceeded."""
        import openai
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Always fail with rate limit error
        def mock_create(**kwargs):
            raise openai.RateLimitError("Rate limit exceeded", response=None, body=None)
        
        mock_client.chat.completions.create = mock_create
        
        # Should raise exception after max retries
        with pytest.raises(Exception):
            client_manager.safe_call(
                mock_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )
    
    def test_is_retryable_error(self, client_manager):
        """Test retryable error detection."""
        import openai
        
        # Rate limit errors should be retryable
        rate_limit_error = openai.RateLimitError("Rate limit", response=None, body=None)
        assert client_manager.is_retryable_error(rate_limit_error) is True
        
        # API connection errors should be retryable
        api_error = openai.APIConnectionError("Connection failed")
        assert client_manager.is_retryable_error(api_error) is True
        
        # Authentication errors should not be retryable
        auth_error = openai.AuthenticationError("Invalid API key", response=None, body=None)
        assert client_manager.is_retryable_error(auth_error) is False
        
        # Generic exceptions should not be retryable
        generic_error = Exception("Generic error")
        assert client_manager.is_retryable_error(generic_error) is False
