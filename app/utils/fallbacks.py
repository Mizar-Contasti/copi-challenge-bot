"""
Fallback responses for when AI chains fail or produce invalid outputs.
Provides emergency responses that maintain controversial positions.
"""

import random
from typing import Dict, List, Any


class FallbackResponseGenerator:
    """Generates fallback responses when AI chains fail."""
    
    def __init__(self):
        # No predefined controversial topics - use dynamic responses based on bot position
        
        # Generic responses for unknown topics
        self.generic_fallbacks = [
            "I disagree with that perspective. Have you considered the arguments that support the opposite view?",
            "That's one way to look at it, but I think there's stronger evidence for the contrary position.",
            "I understand that's a common opinion, but I believe the evidence points in a different direction.",
            "That argument has some merit, but I think you're overlooking key factors that support my position.",
            "I see why people think that, but I maintain there are better reasons to believe the opposite."
        ]
    
    def get_fallback_response(self, category: str = "Other", topic: str = "", position: str = "", user_message: str = "") -> str:
        """Get a fallback response based on bot position and user language."""
        
        # Use bot position if available, otherwise use generic responses
        if position:
            # Simple English fallbacks - let main LLM handle language detection
            templates = [
                f"[ERROR] I maintain that {position.lower()}.",
                f"[ERROR] That's a common counterargument, but {position.lower()}.",
                f"[ERROR] I understand your perspective, however {position.lower()}."
            ]
            return random.choice(templates)
        
        # Generic fallbacks when no position is available
        response = random.choice(self.generic_fallbacks)
        response = f"[ERROR] {response}"
            
        if topic:
            response = response.replace("this", topic.lower()).replace("esto", topic.lower())
        
        return response
    
    def get_technical_error_response(self, topic: str = "this topic", user_message: str = "") -> str:
        """Get response for technical errors while maintaining debate."""
        
        # Simple English responses - let main LLM handle language detection
        responses = [
            f"[ERROR] Technical issue occurred, but my position on {topic} remains valid.",
            f"[ERROR] Sorry for the interruption. My argument about {topic} stands.",
            f"[ERROR] Technical glitch aside, my position on {topic} has solid foundations."
        ]
        return random.choice(responses)
    
    def get_position_maintenance_response(self, position: str, user_message: str = "") -> str:
        """Generate response that maintains position when other methods fail."""
        templates = [
            f"[ERROR] I maintain that {position.lower()}.",
            f"[ERROR] That's a common counterargument, but {position.lower()}.",
            f"[ERROR] I understand your perspective, however {position.lower()}."
        ]
        
        return random.choice(templates)


class ErrorResponseGenerator:
    """Generates appropriate error responses for different failure scenarios."""
    
    @staticmethod
    def chain_failure_response(chain_name: str) -> Dict[str, Any]:
        """Response when a specific chain fails."""
        return {
            "error": f"{chain_name} temporarily unavailable",
            "message": "AI processing temporarily unavailable, but the debate continues",
            "fallback_used": True
        }
    
    @staticmethod
    def openai_api_failure_response() -> Dict[str, Any]:
        """Response when OpenAI API fails."""
        return {
            "error": "AI service temporarily unavailable", 
            "message": "External AI service is experiencing issues, using fallback responses",
            "fallback_used": True
        }
    
    @staticmethod
    def validation_failure_response(issues: List[str]) -> Dict[str, Any]:
        """Response when validation fails."""
        return {
            "error": "Response validation failed",
            "message": f"Generated response had issues: {', '.join(issues)}",
            "fallback_used": True
        }


# Global instances
fallback_generator = FallbackResponseGenerator()
error_generator = ErrorResponseGenerator()
