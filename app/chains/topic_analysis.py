"""
Topic Analysis Chain for identifying conversation topics from user messages.
Analyzes the first user message to determine the debate topic.
"""

from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings


class TopicAnalysisChain:
    """Chain to analyze user messages and identify debate topics."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            request_timeout=settings.openai_timeout_seconds
        )
        
        self.prompt = PromptTemplate(
            input_variables=["user_message"],
            template="""
Analyze this user message to understand what they're discussing and determine how to engage in debate.

User message: "{user_message}"

Tasks:
1. Identify the main topic being discussed
2. Determine if the user has taken a clear position, or if they're asking a neutral question
3. If they have a position, take the opposing stance
4. If they're asking a neutral question (like "which is better X or Y?"), pick one side to defend
5. Keep it reasonable and focused on the actual topic

Return ONLY a JSON object with these fields:
- "topic": Brief topic name (max 50 characters)
- "user_position": What the user believes/argues (or "neutral question" if they haven't taken a stance)
- "bot_position": Your position to argue for (be specific and direct)
- "controversy_level": Number 1-10

Examples:
{{
    "topic": "Remote work productivity",
    "user_position": "Working from home is more productive",
    "bot_position": "Office work is more productive due to better collaboration and fewer distractions",
    "controversy_level": 6
}}

{{
    "topic": "Cola preference",
    "user_position": "neutral question",
    "bot_position": "Pepsi is superior to Coca-Cola due to its sweeter taste and better marketing",
    "controversy_level": 3
}}

Return only the JSON, no markdown formatting or extra text.
"""
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["user_message"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["topic", "user_position", "bot_position", "controversy_level"]
    
    def analyze_topic(self, user_message: str) -> Dict[str, Any]:
        """Analyze user message to identify debate topic."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[TOPIC_ANALYSIS] INPUT: user_message='{user_message}'")
            
            # Format the prompt
            formatted_prompt = self.prompt.format(user_message=user_message)
            logger.debug(f"[TOPIC_ANALYSIS] PROMPT: {formatted_prompt[:200]}...")
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt)
            raw_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[TOPIC_ANALYSIS] LLM_RESPONSE: {raw_response}")
            
            # Parse JSON response - handle markdown code blocks
            import json
            import re
            
            # Remove markdown code blocks if present
            json_text = raw_response.strip()
            if json_text.startswith('```'):
                # Extract JSON from markdown code block
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                else:
                    # Fallback: remove first and last lines if they contain ```
                    lines = json_text.split('\n')
                    if lines[0].strip().startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip().endswith('```'):
                        lines = lines[:-1]
                    json_text = '\n'.join(lines)
            
            result = json.loads(json_text)
            
            output = {
                "topic": result.get("topic", "General Discussion"),
                "user_position": result.get("user_position", "User's stated position"),
                "bot_position": result.get("bot_position", "Contrarian position to be defended"),
                "controversy_level": result.get("controversy_level", 5)
            }
            
            logger.info(f"[TOPIC_ANALYSIS] OUTPUT: {output}")
            return output
            
        except Exception as e:
            logger.error(f"[TOPIC_ANALYSIS] ERROR: {str(e)}")
            # Fallback if analysis fails
            fallback_output = {
                "topic": "General Discussion",
                "user_position": f"User's position: {user_message[:100]}...",
                "bot_position": "I will take a contrarian stance to encourage healthy debate",
                "controversy_level": 5
            }
            logger.info(f"[TOPIC_ANALYSIS] FALLBACK_OUTPUT: {fallback_output}")
            return fallback_output


# Global instance
topic_analysis_chain = TopicAnalysisChain()
