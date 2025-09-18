"""
Hybrid language detection utility for determining user language from messages.
Combines fast manual detection with LLM fallback for ambiguous cases.
"""

from typing import Dict, Any, Tuple
import logging


class HybridLanguageDetector:
    """Hybrid language detection utility with manual + LLM fallback."""
    
    def __init__(self):
        self.spanish_indicators = [
            "qué", "cómo", "por", "para", "con", "sin", "muy", "más", "menos", 
            "también", "sí", "no", "es", "son", "está", "están", "el", "la", 
            "los", "las", "de", "del", "al", "en", "un", "una", "y", "o", 
            "pero", "que", "se", "me", "te", "le", "nos", "os", "les", "mi", 
            "tu", "su", "este", "esta", "estos", "estas", "todo", "todos", 
            "hacer", "tener", "ser", "estar", "ir", "venir", "ver", "dar",
            "carne", "papa", "comida", "casa", "trabajo", "vida", "tiempo",
            "bueno", "malo", "grande", "pequeño", "nuevo", "viejo", "primero"
        ]
        
        self.english_indicators = [
            "the", "and", "or", "but", "is", "are", "was", "were", "have", 
            "has", "had", "do", "does", "did", "will", "would", "could", 
            "should", "can", "may", "might", "must", "shall", "this", "that", 
            "these", "those", "what", "when", "where", "why", "how", "who", 
            "which", "better", "best", "good", "bad", "like", "love", "want", 
            "need", "think", "know", "see", "look", "come", "go", "get", 
            "make", "take", "give", "work", "time", "life", "home", "food",
            "about", "after", "again", "against", "all", "any", "because"
        ]
        
        self.confidence_threshold = 0.7
        self.logger = logging.getLogger(__name__)
    
    def _manual_detection(self, text: str) -> Tuple[str, float]:
        """
        Manual detection with confidence score.
        
        Returns:
            Tuple of (language, confidence)
        """
        if not text:
            return "English", 0.5
        
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)
        
        if total_words == 0:
            return "English", 0.5
        
        spanish_matches = sum(1 for word in self.spanish_indicators if word in text_lower)
        english_matches = sum(1 for word in self.english_indicators if word in text_lower)
        
        # Calculate confidence based on matches and text length
        total_matches = spanish_matches + english_matches
        match_ratio = total_matches / total_words if total_words > 0 else 0
        
        # Base confidence on match ratio and difference between languages
        if spanish_matches > english_matches:
            language = "Spanish"
            confidence = min(0.9, 0.5 + (match_ratio * 0.4) + ((spanish_matches - english_matches) / total_words * 0.3))
        elif english_matches > spanish_matches:
            language = "English"
            confidence = min(0.9, 0.5 + (match_ratio * 0.4) + ((english_matches - spanish_matches) / total_words * 0.3))
        else:
            # Tie or no matches - low confidence
            language = "English"  # Default to English
            confidence = 0.3
        
        return language, confidence
    
    def _llm_detection(self, text: str) -> str:
        """
        LLM-based language detection for ambiguous cases.
        
        Args:
            text: Text to analyze
            
        Returns:
            "Spanish" or "English"
        """
        try:
            from langchain_openai import ChatOpenAI
            from app.config import settings
            
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,  # Low temperature for consistent detection
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url,
                request_timeout=10  # Short timeout for language detection
            )
            
            prompt = f"""Detect the language of this text. Respond with only "Spanish" or "English".

Text: "{text}"

Language:"""
            
            response = llm.invoke(prompt)
            result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            # Clean up response
            if "spanish" in result.lower():
                return "Spanish"
            elif "english" in result.lower():
                return "English"
            else:
                # Fallback if LLM gives unexpected response
                self.logger.warning(f"Unexpected LLM language detection response: {result}")
                return "English"
                
        except Exception as e:
            self.logger.error(f"LLM language detection failed: {e}")
            return "English"  # Fallback to English
    
    def detect_language(self, text: str) -> str:
        """
        Hybrid language detection: fast manual detection with LLM fallback.
        
        Args:
            text: Text to analyze
            
        Returns:
            "Spanish" or "English"
        """
        if not text:
            return "English"
        
        # Step 1: Try manual detection
        language, confidence = self._manual_detection(text)
        
        self.logger.debug(f"Manual detection: {language} (confidence: {confidence:.2f})")
        
        # Step 2: Use LLM if confidence is low
        if confidence >= self.confidence_threshold:
            self.logger.debug(f"High confidence manual detection: {language}")
            return language
        else:
            self.logger.debug(f"Low confidence, using LLM fallback")
            llm_result = self._llm_detection(text)
            self.logger.debug(f"LLM detection result: {llm_result}")
            return llm_result
    
    def get_language_code(self, text: str) -> str:
        """
        Get language code (es/en) from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            "es" or "en"
        """
        language = self.detect_language(text)
        return "es" if language == "Spanish" else "en"


# Global instance
language_detector = HybridLanguageDetector()
