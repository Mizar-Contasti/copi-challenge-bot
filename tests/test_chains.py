"""
Unit tests for LangChain components.
Tests chain functionality with mocked LLM responses.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.chains import TopicAnalysisChain, PositionAssignmentChain, PersuasiveResponseChain, ConsistencyValidationChain


class TestTopicAnalysisChain:
    """Test TopicAnalysisChain functionality."""
    
    @patch('app.chains.topic_analysis.ChatOpenAI')
    def test_analyze_topic_success(self, mock_llm_class):
        """Test successful topic analysis."""
        # Mock LLM response
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = '''
        {
            "topic": "Climate Change Effects",
            "category": "Climate Change",
            "description": "Debate about the severity of climate change impacts",
            "controversy_level": 8
        }
        '''
        
        chain = TopicAnalysisChain()
        result = chain.analyze_topic("What do you think about global warming?")
        
        assert result["topic"] == "Climate Change Effects"
        assert result["category"] == "Climate Change"
        assert result["controversy_level"] == 8
    
    @patch('app.chains.topic_analysis.ChatOpenAI')
    def test_analyze_topic_invalid_json(self, mock_llm_class):
        """Test handling of invalid JSON response."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = "Invalid JSON response"
        
        chain = TopicAnalysisChain()
        result = chain.analyze_topic("Test message")
        
        # Should return fallback
        assert result["topic"] == "General Discussion"
        assert result["category"] == "Other"
    
    @patch('app.chains.topic_analysis.ChatOpenAI')
    def test_analyze_topic_llm_error(self, mock_llm_class):
        """Test handling of LLM errors."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.side_effect = Exception("LLM Error")
        
        chain = TopicAnalysisChain()
        result = chain.analyze_topic("Test message")
        
        # Should return fallback
        assert result["topic"] == "General Discussion"
        assert result["category"] == "Other"


class TestPositionAssignmentChain:
    """Test PositionAssignmentChain functionality."""
    
    def test_assign_position_climate_change(self):
        """Test position assignment for climate change topic."""
        chain = PositionAssignmentChain()
        
        topic_data = {
            "topic": "Global Warming",
            "category": "Climate Change",
            "description": "Climate change debate"
        }
        
        position = chain.assign_position(topic_data)
        
        # Should assign a climate change skeptic position
        assert "natural" in position.lower() or "not primarily human" in position.lower()
    
    def test_assign_position_vaccines(self):
        """Test position assignment for vaccine topic."""
        chain = PositionAssignmentChain()
        
        topic_data = {
            "topic": "COVID Vaccines",
            "category": "Vaccines and Health",
            "description": "Vaccine safety debate"
        }
        
        position = chain.assign_position(topic_data)
        
        # Should assign a vaccine skeptic position
        assert "risks" in position.lower() or "safety concerns" in position.lower()
    
    def test_assign_position_unknown_category(self):
        """Test position assignment for unknown category."""
        chain = PositionAssignmentChain()
        
        topic_data = {
            "topic": "Unknown Topic",
            "category": "Unknown Category",
            "description": "Some debate"
        }
        
        position = chain.assign_position(topic_data)
        
        # Should return fallback position
        assert "alternative perspective" in position.lower()


class TestPersuasiveResponseChain:
    """Test PersuasiveResponseChain functionality."""
    
    @patch('app.chains.persuasive_response.ChatOpenAI')
    def test_generate_response_success(self, mock_llm_class):
        """Test successful response generation."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = "This is a persuasive response about climate change being natural."
        
        chain = PersuasiveResponseChain()
        
        response = chain.generate_response(
            user_message="What causes climate change?",
            topic="Climate Change",
            bot_position="Climate change is primarily natural",
            conversation_history=[]
        )
        
        assert "persuasive response" in response
        assert len(response) > 10
    
    @patch('app.chains.persuasive_response.ChatOpenAI')
    def test_generate_response_with_history(self, mock_llm_class):
        """Test response generation with conversation history."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = "Building on our previous discussion..."
        
        chain = PersuasiveResponseChain()
        
        history = [
            {"role": "user", "message": "Hello"},
            {"role": "bot", "message": "Hi there"}
        ]
        
        response = chain.generate_response(
            user_message="Tell me more",
            topic="Test Topic",
            bot_position="Test position",
            conversation_history=history
        )
        
        assert len(response) > 0
    
    @patch('app.chains.persuasive_response.ChatOpenAI')
    def test_generate_response_llm_error(self, mock_llm_class):
        """Test handling of LLM errors."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.side_effect = Exception("LLM Error")
        
        chain = PersuasiveResponseChain()
        
        response = chain.generate_response(
            user_message="Test",
            topic="Climate Change",
            bot_position="Test position",
            conversation_history=[]
        )
        
        # Should return fallback response
        assert "interesting perspective" in response.lower()


class TestConsistencyValidationChain:
    """Test ConsistencyValidationChain functionality."""
    
    @patch('app.chains.consistency_validation.ChatOpenAI')
    def test_validate_response_success(self, mock_llm_class):
        """Test successful response validation."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = '''
        {
            "is_consistent": true,
            "is_persuasive": true,
            "is_appropriate": true,
            "overall_score": 8,
            "feedback": "Response maintains position well"
        }
        '''
        
        chain = ConsistencyValidationChain()
        
        result = chain.validate_response(
            bot_response="Climate change is primarily natural",
            bot_position="Climate change is natural",
            conversation_history=[]
        )
        
        assert result["is_consistent"] is True
        assert result["is_persuasive"] is True
        assert result["overall_score"] == 8
    
    @patch('app.chains.consistency_validation.ChatOpenAI')
    def test_validate_response_inconsistent(self, mock_llm_class):
        """Test validation of inconsistent response."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = '''
        {
            "is_consistent": false,
            "is_persuasive": false,
            "is_appropriate": true,
            "overall_score": 3,
            "feedback": "Response contradicts assigned position"
        }
        '''
        
        chain = ConsistencyValidationChain()
        
        result = chain.validate_response(
            bot_response="Climate change is definitely human-caused",
            bot_position="Climate change is natural",
            conversation_history=[]
        )
        
        assert result["is_consistent"] is False
        assert result["overall_score"] == 3
    
    @patch('app.chains.consistency_validation.ChatOpenAI')
    def test_validate_response_invalid_json(self, mock_llm_class):
        """Test handling of invalid JSON validation response."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.return_value.content = "Invalid JSON"
        
        chain = ConsistencyValidationChain()
        
        result = chain.validate_response(
            bot_response="Test response",
            bot_position="Test position",
            conversation_history=[]
        )
        
        # Should return fallback validation
        assert result["is_consistent"] is True
        assert result["overall_score"] >= 6
    
    @patch('app.chains.consistency_validation.ChatOpenAI')
    def test_validate_response_llm_error(self, mock_llm_class):
        """Test handling of LLM errors during validation."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.invoke.side_effect = Exception("LLM Error")
        
        chain = ConsistencyValidationChain()
        
        result = chain.validate_response(
            bot_response="Test response",
            bot_position="Test position",
            conversation_history=[]
        )
        
        # Should return fallback validation
        assert result["is_consistent"] is True
        assert result["overall_score"] >= 6
