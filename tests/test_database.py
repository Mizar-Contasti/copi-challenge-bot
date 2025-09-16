"""
Unit tests for database operations and models.
Tests SQLAlchemy models and database manager functionality.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Conversation, Message, DatabaseManager


class TestDatabaseModels:
    """Test SQLAlchemy model functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        engine = create_engine(f"sqlite:///{temp_file.name}")
        Base.metadata.create_all(bind=engine)
        
        yield temp_file.name
        
        os.unlink(temp_file.name)
    
    def test_conversation_model(self, temp_db):
        """Test Conversation model creation and relationships."""
        engine = create_engine(f"sqlite:///{temp_db}")
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            conversation = Conversation(
                id="test-123",
                topic="Climate Change",
                bot_position="Climate change is natural",
                max_turns=2
            )
            session.add(conversation)
            session.commit()
            
            # Retrieve and verify
            retrieved = session.query(Conversation).filter_by(id="test-123").first()
            assert retrieved.topic == "Climate Change"
            assert retrieved.bot_position == "Climate change is natural"
            assert retrieved.max_turns == 2
    
    def test_message_model(self, temp_db):
        """Test Message model creation and validation."""
        engine = create_engine(f"sqlite:///{temp_db}")
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Create conversation first
            conversation = Conversation(
                id="test-123",
                topic="Test Topic",
                bot_position="Test position"
            )
            session.add(conversation)
            session.commit()
            
            # Create message
            message = Message(
                conversation_id="test-123",
                turn=1,
                role="user",
                message="Hello world"
            )
            session.add(message)
            session.commit()
            
            # Retrieve and verify
            retrieved = session.query(Message).filter_by(conversation_id="test-123").first()
            assert retrieved.turn == 1
            assert retrieved.role == "user"
            assert retrieved.message == "Hello world"
    
    def test_message_invalid_role(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValueError):
            Message(
                conversation_id="test-123",
                turn=1,
                role="invalid",
                message="Hello"
            )


class TestDatabaseManager:
    """Test DatabaseManager functionality."""
    
    @pytest.fixture
    def db_manager(self):
        """Create temporary database manager for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Mock settings for testing
        class MockSettings:
            database_url = f"sqlite:///{temp_file.name}"
            log_level = "INFO"
        
        # Create manager with temp database
        manager = DatabaseManager()
        manager.engine = create_engine(MockSettings.database_url)
        manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
        manager.create_tables()
        
        yield manager
        
        os.unlink(temp_file.name)
    
    def test_create_conversation(self, db_manager):
        """Test conversation creation."""
        conversation_id = db_manager.create_conversation(
            topic="Test Topic",
            bot_position="Test Position"
        )
        
        assert conversation_id is not None
        assert len(conversation_id) > 0
        
        # Verify conversation exists
        conversation = db_manager.get_conversation(conversation_id)
        assert conversation is not None
        assert conversation["topic"] == "Test Topic"
        assert conversation["bot_position"] == "Test Position"
        assert conversation["max_turns"] == 0
    
    def test_get_nonexistent_conversation(self, db_manager):
        """Test getting non-existent conversation."""
        conversation = db_manager.get_conversation("nonexistent")
        assert conversation is None
    
    def test_add_message(self, db_manager):
        """Test adding messages to conversation."""
        # Create conversation
        conversation_id = db_manager.create_conversation("Test", "Position")
        
        # Add user message
        success = db_manager.add_message(conversation_id, 1, "user", "Hello")
        assert success is True
        
        # Add bot message (should update max_turns)
        success = db_manager.add_message(conversation_id, 1, "bot", "Hi there")
        assert success is True
        
        # Check max_turns updated
        conversation = db_manager.get_conversation(conversation_id)
        assert conversation["max_turns"] == 1
    
    def test_get_conversation_history(self, db_manager):
        """Test retrieving conversation history."""
        # Create conversation and add messages
        conversation_id = db_manager.create_conversation("Test", "Position")
        
        db_manager.add_message(conversation_id, 1, "user", "Hello")
        db_manager.add_message(conversation_id, 1, "bot", "Hi")
        db_manager.add_message(conversation_id, 2, "user", "How are you?")
        db_manager.add_message(conversation_id, 2, "bot", "Good")
        
        # Get history
        history = db_manager.get_conversation_history(conversation_id)
        
        assert len(history) == 4
        assert history[0]["turn"] == 1
        assert history[0]["role"] == "user"
        assert history[0]["message"] == "Hello"
        assert history[3]["turn"] == 2
        assert history[3]["role"] == "bot"
        assert history[3]["message"] == "Good"
    
    def test_get_current_turn_messages(self, db_manager):
        """Test retrieving messages for specific turn."""
        # Create conversation and add messages
        conversation_id = db_manager.create_conversation("Test", "Position")
        
        db_manager.add_message(conversation_id, 1, "user", "Hello")
        db_manager.add_message(conversation_id, 1, "bot", "Hi")
        db_manager.add_message(conversation_id, 2, "user", "How are you?")
        
        # Get turn 1 messages
        turn_1_messages = db_manager.get_current_turn_messages(conversation_id, 1)
        
        assert len(turn_1_messages) == 2
        assert turn_1_messages[0]["role"] == "user"
        assert turn_1_messages[1]["role"] == "bot"
    
    def test_get_next_turn(self, db_manager):
        """Test getting next turn number."""
        # Create conversation
        conversation_id = db_manager.create_conversation("Test", "Position")
        
        # Should start at turn 1
        next_turn = db_manager.get_next_turn(conversation_id)
        assert next_turn == 1
        
        # Add messages for turn 1
        db_manager.add_message(conversation_id, 1, "user", "Hello")
        db_manager.add_message(conversation_id, 1, "bot", "Hi")
        
        # Should now be turn 2
        next_turn = db_manager.get_next_turn(conversation_id)
        assert next_turn == 2
    
    def test_conversation_exists(self, db_manager):
        """Test conversation existence check."""
        # Non-existent conversation
        assert db_manager.conversation_exists("nonexistent") is False
        
        # Create conversation
        conversation_id = db_manager.create_conversation("Test", "Position")
        
        # Should now exist
        assert db_manager.conversation_exists(conversation_id) is True
