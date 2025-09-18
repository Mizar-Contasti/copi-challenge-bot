"""
Database models and operations for the debate bot application.
Handles SQLite database with conversations and messages tables.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from app.config import settings

Base = declarative_base()


class Conversation(Base):
    """Conversation model with topic, bot position, and turn tracking."""
    
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String, nullable=False)
    bot_position = Column(Text, nullable=False)
    original_topic = Column(Text, nullable=False)  # Store the original user message that started the debate
    max_turns = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model with turn tracking and role (user/bot)."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    turn = Column(Integer, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'bot'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate role
        if self.role not in ['user', 'bot']:
            raise ValueError("Role must be 'user' or 'bot'")


class DatabaseManager:
    """Database manager for handling all database operations."""
    
    def __init__(self):
        self.engine = create_engine(settings.database_url, echo=settings.log_level == "DEBUG")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def create_conversation(self, topic: str, bot_position: str, original_topic: str) -> str:
        """Create a new conversation and return its ID."""
        with self.get_session() as session:
            conversation = Conversation(
                topic=topic,
                bot_position=bot_position,
                original_topic=original_topic
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation.id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                return None
            
            return {
                "id": conversation.id,
                "topic": conversation.topic,
                "bot_position": conversation.bot_position,
                "original_topic": conversation.original_topic,
                "max_turns": conversation.max_turns,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at
            }
    
    def add_message(self, conversation_id: str, turn: int, role: str, message: str) -> bool:
        """Add a message to a conversation."""
        with self.get_session() as session:
            try:
                # Create message
                new_message = Message(
                    conversation_id=conversation_id,
                    turn=turn,
                    role=role,
                    message=message
                )
                session.add(new_message)
                
                # Update max_turns if this is a bot message (end of turn)
                if role == "bot":
                    conversation = session.query(Conversation).filter(
                        Conversation.id == conversation_id
                    ).first()
                    if conversation:
                        conversation.max_turns = max(conversation.max_turns, turn)
                        conversation.updated_at = datetime.utcnow()
                
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error adding message: {e}")
                return False
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation ordered by turn and creation time."""
        with self.get_session() as session:
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.turn, Message.created_at).all()
            
            return [
                {
                    "turn": msg.turn,
                    "role": msg.role,
                    "message": msg.message,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
    
    def get_current_turn_messages(self, conversation_id: str, turn: int) -> List[Dict[str, Any]]:
        """Get messages for a specific turn."""
        with self.get_session() as session:
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.turn == turn
            ).order_by(Message.created_at).all()
            
            return [
                {
                    "turn": msg.turn,
                    "role": msg.role,
                    "message": msg.message,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
    
    def get_next_turn(self, conversation_id: str) -> int:
        """Get the next turn number for a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return 1
        return conversation["max_turns"] + 1
    
    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        return self.get_conversation(conversation_id) is not None


# Global database manager instance
db_manager = DatabaseManager()