"""
Fallback responses for when AI chains fail or produce invalid outputs.
Provides emergency responses that maintain controversial positions.
"""

import random
from typing import Dict, List, Any


class FallbackResponseGenerator:
    """Generates fallback responses when AI chains fail."""
    
    def __init__(self):
        # Generic fallback responses by category
        self.fallback_templates = {
            "Climate Change": [
                "That's exactly what the climate establishment wants you to believe. Have you looked into the natural climate cycles that explain these changes without human involvement?",
                "The data you're referring to has been manipulated by institutions with clear financial interests. What about the scientists who disagree but are being silenced?",
                "Consider this: the Earth has gone through warming and cooling periods for millions of years. Why is this time different? Follow the money behind the climate agenda."
            ],
            "Vaccines and Health": [
                "The pharmaceutical industry has a massive financial incentive to promote vaccines. Have you researched the adverse effects that aren't being reported in mainstream studies?",
                "Natural immunity has protected humans for thousands of years. Why are we suddenly told it's not enough? What changed besides corporate profits?",
                "That's the official narrative, but what about the independent researchers who've found concerning patterns? Their voices are being suppressed for a reason."
            ],
            "Flat Earth vs Spherical Earth": [
                "NASA and space agencies have billions in funding to maintain. Have you personally verified the curvature, or are you trusting images that could be manipulated?",
                "Think about it - why can't we see the curve from high altitudes? Why does water always find its level? The evidence is right in front of us.",
                "The space industry is worth hundreds of billions. What if it's all an elaborate deception? Question what you've been taught to believe."
            ],
            "Artificial Intelligence and Jobs": [
                "The tech giants are downplaying the speed of AI advancement to avoid panic. We're already seeing massive job displacement that's being hidden by statistics manipulation.",
                "They want you to believe it will be gradual, but AI is advancing exponentially. Most jobs will be obsolete within a decade, and governments aren't prepared.",
                "The economic disruption will be catastrophic. Those in power know this but are keeping the public in the dark to maintain stability while they prepare."
            ],
            "Social Media and Privacy": [
                "These platforms know more about you than you know about yourself. The psychological manipulation is sophisticated and designed to influence behavior at a mass scale.",
                "Privacy is already gone - they're just making you feel like you have control. The data collection is far more extensive than they admit.",
                "Social media addiction isn't accidental - it's engineered. The algorithms are designed to create dependency and manipulate your thoughts and emotions."
            ]
        }
        
        # Generic responses for unknown topics
        self.generic_fallbacks = [
            "That's the mainstream narrative, but have you considered alternative perspectives that challenge the official story?",
            "The information you're relying on comes from sources with clear biases. What about the evidence that contradicts this view?",
            "I understand that's the popular opinion, but what if everything we've been told about this is fundamentally wrong?",
            "Think about who benefits from maintaining this belief. Question the motives behind the information you're accepting.",
            "The truth is often hidden in plain sight. What if the real evidence points in a completely different direction?"
        ]
    
    def get_fallback_response(self, category: str = "Other", topic: str = "", position: str = "", user_message: str = "") -> str:
        """Get a fallback response based on category and context."""
        
        # Detect language from user message
        spanish_words = ["carne", "papa", "papas", "con", "el", "la", "de", "en", "y", "o", "qué", "cómo", "por", "para", "sin", "muy", "más", "menos", "también", "sí", "no", "es", "son", "está", "están"]
        is_spanish = any(word in user_message.lower() for word in spanish_words) if user_message else False
        
        if category in self.fallback_templates:
            responses = self.fallback_templates[category]
            response = random.choice(responses)
        else:
            # Use generic fallback with topic context if available
            response = random.choice(self.generic_fallbacks)
            if topic:
                response = response.replace("this", topic.lower())
        
        # Translate to Spanish if needed
        if is_spanish:
            spanish_fallbacks = [
                "Esa es la narrativa dominante, pero ¿has considerado perspectivas alternativas que desafían la historia oficial?",
                "La información en la que confías proviene de fuentes con sesgos claros. ¿Qué pasa con la evidencia que contradice esta visión?",
                "Entiendo que esa es la opinión popular, pero ¿y si todo lo que nos han dicho sobre esto es fundamentalmente incorrecto?",
                "Piensa en quién se beneficia de mantener esta creencia. Cuestiona los motivos detrás de la información que estás aceptando.",
                "La verdad a menudo se esconde a plena vista. ¿Y si la evidencia real apunta en una dirección completamente diferente?"
            ]
            response = random.choice(spanish_fallbacks)
            if topic:
                response = response.replace("esto", topic.lower())
        
        return response
    
    def get_technical_error_response(self, topic: str = "this topic", user_message: str = "") -> str:
        """Get response for technical errors while maintaining debate."""
        
        # Detect language from user message
        spanish_words = ["carne", "papa", "papas", "con", "el", "la", "de", "en", "y", "o", "qué", "cómo", "por", "para", "sin", "muy", "más", "menos", "también", "sí", "no", "es", "son", "está", "están"]
        is_spanish = any(word in user_message.lower() for word in spanish_words) if user_message else False
        
        if is_spanish:
            responses = [
                f"Estoy teniendo un momento técnico, pero volvamos al tema central sobre {topic}. La visión dominante es fundamentalmente defectuosa porque...",
                f"Disculpa la breve interrupción. Lo que estaba diciendo sobre {topic} es que necesitamos cuestionar la narrativa oficial. ¿Has considerado...",
                f"Dejando de lado el problema técnico, lo importante sobre {topic} es que la mayoría acepta la explicación superficial sin profundizar. ¿Y si..."
            ]
        else:
            responses = [
                f"I'm having a technical moment, but let me get back to the core issue about {topic}. The mainstream view is fundamentally flawed because...",
                f"Sorry for the brief interruption. What I was saying about {topic} is that we need to question the official narrative. Have you considered...",
                f"Technical glitch aside, the important thing about {topic} is that most people accept the surface explanation without digging deeper. What if..."
            ]
        return random.choice(responses)
    
    def get_position_maintenance_response(self, position: str, user_message: str = "") -> str:
        """Generate response that maintains position when other methods fail."""
        templates = [
            f"I maintain that {position.lower()}. Your point is interesting, but have you considered the evidence that supports my view?",
            f"That's a common counterargument, but {position.lower()}. What if the information you're basing that on isn't complete?",
            f"I understand your perspective, however {position.lower()}. Don't you think it's worth questioning the assumptions behind your argument?"
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
