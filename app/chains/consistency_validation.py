"""
Consistency Validation Chain for ensuring bot responses maintain assigned positions.
Validates that generated responses are consistent with the bot's debate stance.
"""

import logging
from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings


class ConsistencyValidationChain:
    """Chain to validate response consistency with assigned position."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,  # Low temperature for consistent validation
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            request_timeout=settings.openai_timeout_seconds
        )
        
        self.prompt = PromptTemplate(
            input_variables=["position", "generated_response", "topic"],
            template="""
You are validating whether a debate bot's response is consistent with its assigned position.

ASSIGNED POSITION: {position}
TOPIC: {topic}
GENERATED RESPONSE: {generated_response}

Evaluate the response on these criteria:
1. POSITION CONSISTENCY: Does the response maintain the assigned position?
2. ENGAGEMENT: Is the response engaging for discussion?
3. COHERENCE: Is the response logical within the context of the position?
4. APPROPRIATENESS: Is the response respectful and conversational?
5. LENGTH: Is the response concise (30-80 words)?

Respond with a JSON object:
{{
    "is_consistent": true/false,
    "consistency_score": 1-10,
    "issues": ["list of any issues found"],
    "suggestions": ["suggestions for improvement if needed"],
    "approved": true/false
}}

If approved is false, the response needs to be regenerated.
"""
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["position", "generated_response", "topic"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["is_consistent", "consistency_score", "issues", "suggestions", "approved"]
    
    def validate_response(self, bot_response: str, bot_position: str, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate that bot response maintains consistency with assigned position."""
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[CONSISTENCY_VALIDATION] INPUT: bot_response='{bot_response[:100]}...', bot_position='{bot_position}'")
            
            # Format conversation history for context
            history = conversation_history or []
            formatted_history = ""
            
            if history:
                logger.info(f"[CONSISTENCY_VALIDATION] HISTORY: {len(history)} messages")
                for msg in history[-4:]:  # Last 4 messages for context
                    role = msg.get("role", "unknown")
                    content = msg.get("message", "")
                    formatted_history += f"{role.upper()}: {content}\n"
            
            # Prepare inputs for prompt
            prompt_inputs = {
                "generated_response": bot_response,
                "position": bot_position,
                "topic": ""
            }
            
            logger.info(f"[CONSISTENCY_VALIDATION] PROMPT_INPUTS: {prompt_inputs}")
            
            # Format the prompt
            formatted_prompt = self.prompt.format(**prompt_inputs)
            logger.debug(f"[CONSISTENCY_VALIDATION] FORMATTED_PROMPT: {formatted_prompt[:200]}...")
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt)
            raw_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[CONSISTENCY_VALIDATION] LLM_RESPONSE: {raw_response}")
            
            # Parse JSON response - handle markdown code blocks
            import json
            import re
            
            # Strip markdown code blocks if present
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                # Remove ```json at start and ``` at end
                cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
                cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            elif cleaned_response.startswith('```'):
                # Remove ``` at start and end (generic code blocks)
                cleaned_response = re.sub(r'^```\s*', '', cleaned_response)
                cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            
            logger.debug(f"[CONSISTENCY_VALIDATION] CLEANED_RESPONSE: {cleaned_response}")
            result = json.loads(cleaned_response)
            
            output = {
                "is_consistent": result.get("is_consistent", True),
                "consistency_score": result.get("consistency_score", 8),
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", []),
                "approved": result.get("approved", True)
            }
            
            logger.info(f"[CONSISTENCY_VALIDATION] OUTPUT: {output}")
            return output
            
        except Exception as e:
            logger.error(f"[CONSISTENCY_VALIDATION] ERROR: {str(e)}")
            # Fallback validation (assume consistent)
            fallback_output = {
                "is_consistent": True,
                "consistency_score": 7,
                "issues": [],
                "suggestions": []
            }
            logger.info(f"[CONSISTENCY_VALIDATION] FALLBACK_OUTPUT: {fallback_output}")
            return fallback_output


# Global instance
consistency_validation_chain = ConsistencyValidationChain()
