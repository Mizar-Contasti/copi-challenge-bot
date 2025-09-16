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
Analyze the following user message and identify the main topic for a debate.

User message: "{user_message}"

Your task is to:
1. Identify the core topic or subject matter
2. Determine if it relates to any controversial subjects
3. Classify the topic into one of these categories or create a new one:
   - Climate Change
   - Vaccines and Health
   - Flat Earth vs Spherical Earth
   - Artificial Intelligence and Jobs
   - Social Media and Privacy
   - Other (specify)

Respond with a JSON object containing:
- "topic": Brief topic name (max 50 characters)
- "category": One of the categories above
- "description": Detailed description of what the debate should focus on
- "controversy_level": Scale 1-10 (10 being most controversial)

Example response:
{{
    "topic": "Human-caused climate change",
    "category": "Climate Change", 
    "description": "Debate about whether climate change is primarily caused by human activities or natural phenomena",
    "controversy_level": 8
}}

Only respond with the JSON object, no additional text.
"""
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["user_message"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["topic", "category", "description", "controversy_level"]
    
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
            
            # Parse JSON response
            import json
            result = json.loads(raw_response)
            
            output = {
                "topic": result.get("topic", "General Discussion"),
                "category": result.get("category", "Other"),
                "description": result.get("description", "General debate topic"),
                "controversy_level": result.get("controversy_level", 5)
            }
            
            logger.info(f"[TOPIC_ANALYSIS] OUTPUT: {output}")
            return output
            
        except Exception as e:
            logger.error(f"[TOPIC_ANALYSIS] ERROR: {str(e)}")
            # Fallback if analysis fails
            fallback_output = {
                "topic": "General Discussion",
                "category": "Other", 
                "description": f"Debate about: {user_message[:100]}...",
                "controversy_level": 5
            }
            logger.info(f"[TOPIC_ANALYSIS] FALLBACK_OUTPUT: {fallback_output}")
            return fallback_output


# Global instance
topic_analysis_chain = TopicAnalysisChain()
