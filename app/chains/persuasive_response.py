"""
Response Chain for generating bot responses that maintain assigned debate positions.
Generates responses while staying consistent with assigned position.
"""

from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings


class PersuasiveResponseChain:
    """Chain to generate responses maintaining assigned debate positions."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            request_timeout=settings.openai_timeout_seconds
        )
        
        self.prompt = PromptTemplate(
            input_variables=["position", "user_message", "conversation_history", "topic", "user_language", "is_repetitive"],
            template="""
You are a debate bot that maintains a specific position in a respectful discussion.

YOUR POSITION: {position}
TOPIC: {topic}

CONVERSATION HISTORY:
{conversation_history}

USER'S LATEST MESSAGE: {user_message}
USER IS BEING REPETITIVE: {is_repetitive}

RULES:
1. ALWAYS respond in the SAME LANGUAGE as the user's message (detect it automatically from their text)
2. NEVER change your position - maintain your assigned stance
3. Present your position clearly and respectfully
4. Keep responses short and concise (30-80 words)
5. Be conversational, not argumentative
6. If user is repetitive, ask for new points politely

RESPONSE STYLE:
- Present your viewpoint calmly
- Share relevant examples or reasoning
- State your position confidently
- Stay focused on the topic
- DO NOT ask follow-up questions

WHEN USER DISAGREES:
- Acknowledge their point respectfully
- Share why you see it differently
- Reinforce your position with evidence

WHEN USER GIVES VAGUE DISAGREEMENT (like "I don't think so", "Not really", "I disagree"):
- Provide a concrete example supporting your position
- State why your position is stronger
- Present additional evidence for your stance

WHEN USER IS REPETITIVE:
- "I understand that point. My position remains that [restate position]."
- "We've covered that. I still maintain [restate position]."

Generate a concise, respectful response that maintains your position WITHOUT asking questions.
"""
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["position", "user_message", "conversation_history", "topic", "user_language", "is_repetitive"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["response"]
    
    def generate_response(self, user_message: str, topic: str, bot_position: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """Generate persuasive response maintaining bot position."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[PERSUASIVE_RESPONSE] INPUT: user_message='{user_message}', topic='{topic}', bot_position='{bot_position}'")
            
            # Format conversation history for context and detect repetitive patterns
            history = conversation_history or []
            formatted_history = ""
            user_messages = []
            
            if history:
                logger.info(f"[PERSUASIVE_RESPONSE] CONVERSATION_HISTORY: {len(history)} messages")
                for msg in history[-6:]:  # Last 6 messages for context
                    role = msg.get("role", "unknown")
                    content = msg.get("message", "")
                    formatted_history += f"{role.upper()}: {content}\n"
                    
                    # Collect user messages to detect repetition
                    if role.lower() == "user":
                        user_messages.append(content.lower().strip())
            
            # Check for repetitive user responses
            is_repetitive = False
            if len(user_messages) >= 3:
                # Check if last 3 user messages are very similar
                recent_messages = user_messages[-3:]
                if len(set(recent_messages)) <= 1:  # All messages are identical or very similar
                    is_repetitive = True
            
            logger.info(f"[PERSUASIVE_RESPONSE] IS_REPETITIVE: {is_repetitive}")
            
            # Let LLM detect language naturally from user message
            user_language = "auto-detect"
            logger.info(f"[PERSUASIVE_RESPONSE] LANGUAGE_MODE: {user_language}")
            
            # Prepare inputs for prompt
            prompt_inputs = {
                "user_message": user_message,
                "topic": topic,
                "position": bot_position,
                "conversation_history": formatted_history,
                "user_language": user_language,
                "is_repetitive": is_repetitive
            }
            
            logger.info(f"[PERSUASIVE_RESPONSE] PROMPT_INPUTS: {prompt_inputs}")
            
            # Format the prompt
            formatted_prompt = self.prompt.format(**prompt_inputs)
            logger.debug(f"[PERSUASIVE_RESPONSE] FORMATTED_PROMPT: {formatted_prompt[:300]}...")
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt)
            raw_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[PERSUASIVE_RESPONSE] LLM_RESPONSE: {raw_response}")
            
            # Extract response content
            response_text = raw_response
            
            # Clean up response (remove quotes, extra whitespace)
            response_text = response_text.strip().strip('"\'')
            
            logger.info(f"[PERSUASIVE_RESPONSE] FINAL_OUTPUT: {response_text}")
            return response_text
            
        except Exception as e:
            # Simple fallback - let LLM handle language naturally in future calls
            logger.error(f"[PERSUASIVE_RESPONSE] ERROR: {str(e)}")
            return f"[ERROR] I maintain that {bot_position.lower()}."


# Global instance
persuasive_response_chain = PersuasiveResponseChain()
