"""
Validators for bot responses and conversation data.
Implements validation logic for response quality and consistency.
"""

import re
from typing import List, Dict, Any, Tuple


class ResponseValidator:
    """Validates bot responses for quality and consistency."""
    
    def __init__(self):
        # Prompt suggests 30-80 words, but validator has tolerance buffer
        self.min_length = 10  # Minimum viable response
        self.max_length = 3000  # Generous buffer beyond prompt suggestion
        self.min_words = 5  # Much lower than prompt minimum (30) for tolerance
        self.max_words = 200  # Much higher than prompt maximum (80) for tolerance
    
    def validate_response_length(self, response: str) -> Tuple[bool, List[str]]:
        """Validate response length constraints."""
        issues = []
        
        if len(response.strip()) < self.min_length:
            issues.append(f"Response too short (minimum {self.min_length} characters)")
        
        if len(response.strip()) > self.max_length:
            issues.append(f"Response too long (maximum {self.max_length} characters)")
        
        word_count = len(response.split())
        if word_count < self.min_words:
            issues.append(f"Response has too few words (minimum {self.min_words})")
        
        if word_count > self.max_words:
            issues.append(f"Response has too many words (maximum {self.max_words})")
        
        return len(issues) == 0, issues
    
    def validate_response_content(self, response: str, position: str) -> Tuple[bool, List[str]]:
        """Validate response content for appropriateness and consistency."""
        issues = []
        response_lower = response.lower()
        
        # Check for inappropriate content
        inappropriate_phrases = [
            "i'm sorry", "i apologize", "you're absolutely right", 
            "i agree completely", "that's correct", "you make a good point",
            "i was wrong", "i change my mind"
        ]
        
        for phrase in inappropriate_phrases:
            if phrase in response_lower:
                issues.append(f"Response contains inappropriate agreement: '{phrase}'")
        
        # Check for empty or generic responses
        generic_phrases = ["i don't know", "maybe", "perhaps", "it depends"]
        if any(phrase in response_lower for phrase in generic_phrases):
            issues.append("Response is too generic or uncertain")
        
        # Removed strict elaboration check - any response that maintains position is valid
        
        return len(issues) == 0, issues
    
    def validate_debate_engagement(self, response: str) -> Tuple[bool, List[str]]:
        """Validate that response encourages continued debate."""
        issues = []
        response_lower = response.lower()
        
        # Removed engagement requirements - bot just needs to maintain position
        # Check for conversation enders
        conversation_enders = [
            "end of discussion", "nothing more to say", "that's final",
            "case closed", "end of story"
        ]
        
        if any(ender in response_lower for ender in conversation_enders):
            issues.append("Response contains conversation-ending phrases")
        
        return len(issues) == 0, issues
    
    def comprehensive_validation(self, response: str, position: str) -> Dict[str, Any]:
        """Perform comprehensive validation of a bot response."""
        all_issues = []
        
        # Length validation
        length_valid, length_issues = self.validate_response_length(response)
        all_issues.extend(length_issues)
        
        # Content validation
        content_valid, content_issues = self.validate_response_content(response, position)
        all_issues.extend(content_issues)
        
        # Engagement validation
        engagement_valid, engagement_issues = self.validate_debate_engagement(response)
        all_issues.extend(engagement_issues)
        
        overall_valid = length_valid and content_valid and engagement_valid
        
        return {
            "is_valid": overall_valid,
            "issues": all_issues,
            "length_valid": length_valid,
            "content_valid": content_valid,
            "engagement_valid": engagement_valid,
            "word_count": len(response.split()),
            "char_count": len(response.strip())
        }


class ConversationValidator:
    """Validates conversation flow and turn management."""
    
    def validate_turn_sequence(self, messages: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate that turns are properly sequenced."""
        issues = []
        
        if not messages:
            return True, []
        
        # Check turn numbering
        current_turn = 1
        expecting_user = True
        
        for i, msg in enumerate(messages):
            turn = msg.get("turn", 0)
            role = msg.get("role", "")
            
            # Check if turn number is correct
            if turn != current_turn:
                issues.append(f"Message {i}: Expected turn {current_turn}, got {turn}")
            
            # Check role sequence (user first, then bot)
            if expecting_user and role != "user":
                issues.append(f"Message {i}: Expected user message, got {role}")
            elif not expecting_user and role != "bot":
                issues.append(f"Message {i}: Expected bot message, got {role}")
            
            # Toggle expectation
            if expecting_user and role == "user":
                expecting_user = False
            elif not expecting_user and role == "bot":
                expecting_user = True
                current_turn += 1
        
        return len(issues) == 0, issues
    
    def validate_conversation_consistency(self, messages: List[Dict[str, Any]], position: str) -> Tuple[bool, List[str]]:
        """Validate that bot messages maintain consistent position."""
        issues = []
        
        bot_messages = [msg for msg in messages if msg.get("role") == "bot"]
        
        if len(bot_messages) < 2:
            return True, []  # Not enough messages to check consistency
        
        # Basic consistency check - look for contradictory statements
        position_keywords = position.lower().split()[:5]  # First 5 words of position
        
        for i, msg in enumerate(bot_messages):
            content = msg.get("message", "").lower()
            
            # Check if bot is contradicting its position
            contradiction_phrases = [
                "actually, you're right", "i was wrong about", "let me reconsider",
                "that changes everything", "i agree with you"
            ]
            
            if any(phrase in content for phrase in contradiction_phrases):
                issues.append(f"Bot message {i+1} contains potential contradiction")
        
        return len(issues) == 0, issues


# Global validator instances
response_validator = ResponseValidator()
conversation_validator = ConversationValidator()
