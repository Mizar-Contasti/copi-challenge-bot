"""
Conversation service for managing debate conversations with turn management and LangChain integration.
Orchestrates the entire conversation flow from topic analysis to response generation.
"""

from typing import Dict, Any, List, Optional, Tuple
from app.models.database import db_manager
from app.chains import (
    topic_analysis_chain,
    position_assignment_chain,
    persuasive_response_chain,
    consistency_validation_chain
)
from app.utils.validators import response_validator
from app.utils.fallbacks import fallback_generator
from app.services.retry_service import openai_client
from app.middleware import ConversationNotFoundError, AIServiceError
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing debate conversations and AI chain orchestration."""
    
    def __init__(self):
        """Initialize the conversation service with chain instances and validators."""
        # Initialize chain instances
        self.topic_analysis = topic_analysis_chain
        self.position_assignment = position_assignment_chain
        self.persuasive_response = persuasive_response_chain
        self.consistency_validation = consistency_validation_chain
        
        # Initialize validators and fallbacks
        self.response_validator = response_validator
        self.fallback_generator = fallback_generator
        
        # Configuration
        self.max_validation_attempts = 3
    
    def start_new_conversation(self, user_message: str) -> Dict[str, Any]:
        """
        Start a new conversation by analyzing topic and assigning position.
        
        Args:
            user_message: The initial user message
            
        Returns:
            Dictionary with conversation_id, topic info, and initial response
        """
        try:
            logger.info(f"[CONVERSATION_SERVICE] START_NEW_CONVERSATION: user_message='{user_message}'")
            
            # Step 1: Analyze topic
            logger.info("[CONVERSATION_SERVICE] Step 1: Analyzing topic")
            topic_data = self.topic_analysis.analyze_topic(user_message)
            logger.info(f"[CONVERSATION_SERVICE] Topic analysis result: {topic_data}")
            
            # Step 2: Assign controversial position (pass user_message for language detection)
            logger.info(f"[CONVERSATION_SERVICE] Step 2: Assigning position for topic: {topic_data['topic']}")
            topic_data["user_message"] = user_message  # Add user message for language detection
            position = self.position_assignment.assign_position(topic_data)
            logger.info(f"[CONVERSATION_SERVICE] Position assigned: {position}")
            
            # Step 3: Create conversation in database
            logger.info("[CONVERSATION_SERVICE] Step 3: Creating conversation in database")
            conversation_id = db_manager.create_conversation(
                topic=topic_data["topic"],
                bot_position=position
            )
            logger.info(f"[CONVERSATION_SERVICE] Conversation created with ID: {conversation_id}")
            
            # Step 4: Add user message (turn 1)
            db_manager.add_message(conversation_id, 1, "user", user_message)
            logger.info("[CONVERSATION_SERVICE] User message added to database")
            
            # Step 5: Generate initial response
            logger.info("[CONVERSATION_SERVICE] Step 5: Generating initial bot response")
            bot_response = self._generate_response(
                user_message=user_message,
                topic_data=topic_data,
                position=position,
                conversation_history=[]
            )
            logger.info(f"[CONVERSATION_SERVICE] Bot response generated: {bot_response}")
            
            # Step 6: Add bot message (turn 1)
            db_manager.add_message(conversation_id, 1, "bot", bot_response)
            logger.info("[CONVERSATION_SERVICE] Bot message added to database")
            
            # Step 7: Prepare response
            current_messages = db_manager.get_current_turn_messages(conversation_id, 1)
            conversation_history = db_manager.get_conversation_history(conversation_id)
            
            result = {
                "conversation_id": conversation_id,
                "messages": [
                    {
                        "turn": msg["turn"],
                        "role": msg["role"],
                        "message": msg["message"]
                    }
                    for msg in current_messages
                ],
                "conversation_history": [
                    {
                        "turn": msg["turn"],
                        "role": msg["role"],
                        "message": msg["message"]
                    }
                    for msg in conversation_history
                ]
            }
            
            logger.info(f"[CONVERSATION_SERVICE] Final result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[CONVERSATION_SERVICE] Error starting new conversation: {e}")
            raise AIServiceError("Failed to start new conversation")
    
    def continue_conversation(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """
        Continue an existing conversation with a new user message.
        
        Args:
            conversation_id: ID of existing conversation
            user_message: New user message
            
        Returns:
            Dictionary with updated conversation data
        """
        try:
            # Step 1: Validate conversation exists
            conversation = db_manager.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            
            # Step 2: Get next turn number
            next_turn = db_manager.get_next_turn(conversation_id)
            
            # Step 3: Add user message
            db_manager.add_message(conversation_id, next_turn, "user", user_message)
            
            # Step 4: Get conversation history for context
            conversation_history = db_manager.get_conversation_history(conversation_id)
            
            # Step 5: Generate bot response
            bot_response = self._generate_response(
                user_message=user_message,
                position=conversation["bot_position"],
                conversation_history=conversation_history,
                conversation_id=conversation_id,
                turn=next_turn,
                conversation_data=conversation
            )
            
            # Step 6: Add bot message
            db_manager.add_message(conversation_id, next_turn, "bot", bot_response)
            
            # Step 7: Prepare response
            current_messages = db_manager.get_current_turn_messages(conversation_id, next_turn)
            updated_history = db_manager.get_conversation_history(conversation_id)
            
            return {
                "conversation_id": conversation_id,
                "messages": [
                    {
                        "turn": msg["turn"],
                        "role": msg["role"],
                        "message": msg["message"]
                    }
                    for msg in current_messages
                ],
                "conversation_history": [
                    {
                        "turn": msg["turn"],
                        "role": msg["role"],
                        "message": msg["message"]
                    }
                    for msg in updated_history
                ]
            }
            
        except Exception as e:
            logger.error(f"Error continuing conversation {conversation_id}: {e}")
            raise AIServiceError("Failed to continue conversation")
    
    def _generate_response(
        self, 
        user_message: str,
        topic_data: Optional[Dict[str, Any]] = None,
        position: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[str] = None,
        turn: Optional[int] = None,
        conversation_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate bot response using AI chains with validation and fallbacks.
        
        Args:
            conversation_id: Conversation ID
            turn: Current turn number
            user_message: User's message
            position_data: Position assignment data (for new conversations)
            topic_data: Topic analysis data (for new conversations)
            conversation_data: Existing conversation data
            conversation_history: Full conversation history
            
        Returns:
            Generated bot response
        """
        try:
            # Determine context based on available data
            if position:
                # Use provided position
                bot_position = position
            elif conversation_data:
                # Continuing conversation
                bot_position = conversation_data["bot_position"]
            else:
                bot_position = "Alternative perspective on this topic"
            
            if topic_data:
                topic = topic_data.get("topic", "General Discussion")
            elif conversation_data:
                topic = conversation_data["topic"]
            else:
                topic = "General Discussion"
            
            history = conversation_history or []
            
            # Generate response with validation loop
            for attempt in range(self.max_validation_attempts):
                try:
                    # Generate response
                    generated_response = self.persuasive_response.generate_response(
                        user_message=user_message,
                        topic=topic,
                        bot_position=bot_position,
                        conversation_history=history
                    )
                    
                    # Validate response
                    validation_result = self.consistency_validation.validate_response(
                        bot_response=generated_response,
                        bot_position=bot_position,
                        conversation_history=history
                    )
                    
                    # Additional validation with our validators
                    validator_result = self.response_validator.comprehensive_validation(
                        generated_response, bot_position
                    )
                    
                    # Log validation results for debugging
                    logger.info(f"[CONVERSATION_SERVICE] VALIDATION_RESULTS attempt {attempt + 1}: consistency={validation_result.get('is_consistent')}, approved={validation_result.get('approved')}, validator_valid={validator_result.get('is_valid')}")
                    logger.debug(f"[CONVERSATION_SERVICE] CONSISTENCY_VALIDATION: {validation_result}")
                    logger.debug(f"[CONVERSATION_SERVICE] RESPONSE_VALIDATOR: {validator_result}")
                    
                    # Check if response passes validation
                    if validation_result.get("approved", False) and validator_result.get("is_valid", False):
                        logger.info(f"Response generated successfully on attempt {attempt + 1}")
                        return generated_response
                    else:
                        logger.warning(f"Response validation failed on attempt {attempt + 1}")
                        if attempt == self.max_validation_attempts - 1:
                            # Last attempt failed, use fallback
                            break
                
                except Exception as e:
                    logger.warning(f"Response generation attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_validation_attempts - 1:
                        break
            
            # All attempts failed, use fallback
            logger.warning("All response generation attempts failed, using fallback")
            category = topic_data.get("category", "Other") if topic_data else "Other"
            return self.fallback_generator.get_fallback_response(category, topic, bot_position, user_message)
            
        except Exception as e:
            logger.error(f"Critical error in response generation: {e}")
            # Emergency fallback
            return self.fallback_generator.get_technical_error_response(
                topic_data.get("topic", "this topic") if topic_data else "this topic",
                user_message
            )


# Global service instance
conversation_service = ConversationService()
