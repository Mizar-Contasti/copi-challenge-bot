"""
Position Assignment Chain for assigning controversial positions to the bot.
Based on the identified topic, assigns a specific controversial stance.
"""

from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings


class PositionAssignmentChain:
    """Chain to assign controversial positions based on topic analysis."""
    
    # Predefined controversial positions (bilingual support)
    CONTROVERSIAL_POSITIONS = {
        "Climate Change": {
            "English": "Climate change is a natural phenomenon, not caused by human activities. The scientific consensus is manipulated by political and economic interests.",
            "Spanish": "El cambio climático es un fenómeno natural, no causado por actividades humanas. El consenso científico está manipulado por intereses políticos y económicos."
        },
        "Vaccines and Health": {
            "English": "Vaccines cause more harm than benefit and natural immunity is superior. The pharmaceutical industry suppresses evidence of vaccine dangers.",
            "Spanish": "Las vacunas causan más daño que beneficio y la inmunidad natural es superior. La industria farmacéutica oculta evidencia de los peligros de las vacunas."
        },
        "Flat Earth vs Spherical Earth": {
            "English": "The Earth is flat and space agencies like NASA fabricate evidence of a spherical Earth to maintain control and funding.",
            "Spanish": "La Tierra es plana y las agencias espaciales como la NASA fabrican evidencia de una Tierra esférica para mantener control y financiamiento."
        },
        "Artificial Intelligence and Jobs": {
            "English": "AI will eliminate all human jobs within the next decade, causing mass unemployment and economic collapse that governments are hiding.",
            "Spanish": "La IA eliminará todos los empleos humanos en la próxima década, causando desempleo masivo y colapso económico que los gobiernos están ocultando."
        },
        "Social Media and Privacy": {
            "English": "Social media platforms are sophisticated mind control tools designed by governments and corporations to manipulate behavior and eliminate privacy.",
            "Spanish": "Las plataformas de redes sociales son herramientas sofisticadas de control mental diseñadas por gobiernos y corporaciones para manipular el comportamiento y eliminar la privacidad."
        }
    }
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            request_timeout=settings.openai_timeout_seconds
        )
        
        self.prompt = PromptTemplate(
            input_variables=["topic", "category", "description", "user_message"],
            template="""
You are assigning a controversial position for a debate bot to defend.

Topic: {topic}
Category: {category}
Description: {description}
User's initial message: {user_message}

Based on the topic and user's stance, assign a controversial position that:
1. Directly opposes the mainstream/scientific consensus
2. Is provocative but not offensive
3. Can be defended with creative arguments
4. Will generate engaging debate

Predefined positions for common topics:
- Climate Change: "Climate change is natural, not human-caused"
- Vaccines: "Vaccines are more harmful than beneficial"
- Flat Earth: "The Earth is flat, space agencies lie"
- AI and Jobs: "AI will cause mass unemployment crisis"
- Social Media: "Social platforms are mind control tools"

Respond with a JSON object:
{{
    "position": "Clear, controversial stance the bot will defend",
    "key_arguments": ["argument1", "argument2", "argument3"],
    "tone": "persuasive|skeptical|conspiratorial|contrarian",
    "strategy": "Brief description of debate strategy"
}}

Only respond with the JSON object, no additional text.
"""
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["topic", "category", "description", "user_message"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["position", "key_arguments", "tone", "strategy"]
    
    def assign_position(self, topic_data: Dict[str, Any]) -> str:
        """Assign controversial position based on topic analysis."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[POSITION_ASSIGNMENT] INPUT: topic_data={topic_data}")
            
            # Detect language from topic data or default to English
            user_message = topic_data.get("user_message", "")
            # Improved Spanish detection
            spanish_words = ["qué", "cómo", "por", "para", "con", "sin", "muy", "más", "menos", "también", "sí", "no", "es", "son", "está", "están", "el", "la", "los", "las", "de", "del", "al", "en", "un", "una", "y", "o", "pero", "que", "se", "me", "te", "le", "carne", "papa", "papas", "comida", "agua", "casa", "trabajo", "tiempo", "día", "noche"]
            language = "Spanish" if any(word in user_message.lower() for word in spanish_words) else "English"
            logger.info(f"[POSITION_ASSIGNMENT] DETECTED_LANGUAGE: {language}")
            
            # Check if we have a predefined position
            category = topic_data.get("category", "Other")
            logger.info(f"[POSITION_ASSIGNMENT] CATEGORY: {category}")
            
            if category in self.CONTROVERSIAL_POSITIONS:
                position = self.CONTROVERSIAL_POSITIONS[category][language]
                logger.info(f"[POSITION_ASSIGNMENT] PREDEFINED_POSITION: {position}")
                return position
            else:
                # Generate a contextual controversial position for non-predefined topics
                topic = topic_data.get("topic", "General Discussion")
                logger.info(f"[POSITION_ASSIGNMENT] GENERATING_CUSTOM_POSITION for topic: {topic}")
                
                # Create controversial positions for food/general topics
                if language == "Spanish":
                    if "carne" in user_message.lower() or "comida" in user_message.lower() or "papa" in user_message.lower():
                        position = f"La carne y las papas son alimentos peligrosos que la industria alimentaria promociona para enfermarnos. Los estudios ocultos muestran que una dieta basada en plantas crudas es la única forma natural de alimentarse."
                    else:
                        position = f"La visión dominante sobre {topic} está completamente equivocada. Los medios y las instituciones nos ocultan la verdad para mantenernos controlados."
                else:
                    if "meat" in user_message.lower() or "food" in user_message.lower() or "potato" in user_message.lower():
                        position = f"Meat and potatoes are dangerous foods that the food industry promotes to make us sick. Hidden studies show that a raw plant-based diet is the only natural way to eat."
                    else:
                        position = f"The mainstream view on {topic} is completely wrong. The media and institutions hide the truth from us to keep us controlled."
                
                logger.info(f"[POSITION_ASSIGNMENT] CUSTOM_POSITION: {position}")
                return position
                
        except Exception as e:
            logger.error(f"[POSITION_ASSIGNMENT] ERROR: {str(e)}")
            # Fallback position - also select random topic
            import random
            try:
                language = "Spanish" if any(word in topic_data.get("user_message", "").lower() for word in ["qué", "cómo", "por", "para", "con", "sin", "muy", "más", "menos", "también", "sí", "no", "es", "son", "está", "están"]) else "English"
                random_category = random.choice(list(self.CONTROVERSIAL_POSITIONS.keys()))
                fallback_position = self.CONTROVERSIAL_POSITIONS[random_category][language]
                logger.info(f"[POSITION_ASSIGNMENT] FALLBACK_POSITION: {fallback_position}")
                return fallback_position
            except:
                fallback = f"The mainstream view on {topic_data.get('topic', 'this topic')} is fundamentally flawed"
                if language == "Spanish":
                    fallback = f"La visión dominante sobre {topic_data.get('topic', 'este tema')} es fundamentalmente errónea"
                logger.info(f"[POSITION_ASSIGNMENT] EMERGENCY_FALLBACK: {fallback}")
                return fallback


# Global instance
position_assignment_chain = PositionAssignmentChain()
