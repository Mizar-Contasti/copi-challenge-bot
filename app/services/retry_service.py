"""
Retry service for handling OpenAI API failures with exponential backoff.
Implements robust error handling and retry logic for external API calls.
"""

import time
import random
from typing import Any, Callable, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, RateLimitError, APITimeoutError, APIError, AuthenticationError
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RetryService:
    """Service for handling retries and error management for OpenAI API calls."""
    
    def __init__(self):
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay_seconds
        self.timeout = settings.openai_timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        reraise=True
    )
    def call_openai_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute OpenAI API call with retry logic.
        
        Args:
            func: The function to call (e.g., client.chat.completions.create)
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            API response
            
        Raises:
            AuthenticationError: For auth issues (no retry)
            Exception: For other unrecoverable errors
        """
        try:
            return func(*args, **kwargs)
        except AuthenticationError as e:
            logger.error(f"OpenAI Authentication error: {e}")
            raise  # Don't retry auth errors
        except RateLimitError as e:
            logger.warning(f"OpenAI Rate limit hit: {e}")
            # Add jitter to avoid thundering herd
            time.sleep(random.uniform(1, 3))
            raise  # Will be retried by tenacity
        except APITimeoutError as e:
            logger.warning(f"OpenAI Timeout: {e}")
            raise  # Will be retried by tenacity
        except APIError as e:
            logger.warning(f"OpenAI API error: {e}")
            raise  # Will be retried by tenacity
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise
    
    def safe_openai_call(self, func: Callable, fallback_value: Any = None, *args, **kwargs) -> tuple[Any, bool]:
        """
        Make a safe OpenAI API call with fallback.
        
        Args:
            func: The function to call
            fallback_value: Value to return if all retries fail
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Tuple of (result, success_flag)
        """
        try:
            result = self.call_openai_with_retry(func, *args, **kwargs)
            return result, True
        except AuthenticationError:
            logger.error("OpenAI authentication failed - check API key")
            return fallback_value, False
        except Exception as e:
            logger.error(f"OpenAI call failed after retries: {e}")
            return fallback_value, False


class OpenAIClientManager:
    """Manages OpenAI client with proper configuration and error handling."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds
        )
        self.retry_service = RetryService()
    
    def chat_completion(self, messages: list, model: str = "gpt-4o", **kwargs) -> tuple[Optional[str], bool]:
        """
        Create a chat completion with retry logic.
        
        Args:
            messages: List of message dicts
            model: OpenAI model to use
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (response_content, success_flag)
        """
        def _call():
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        
        return self.retry_service.safe_openai_call(_call, fallback_value=None)
    
    def validate_api_key(self) -> bool:
        """Validate that the OpenAI API key is working."""
        try:
            response, success = self.chat_completion([
                {"role": "user", "content": "Hello"}
            ])
            return success and response is not None
        except Exception:
            return False


# Global client manager instance
openai_client = OpenAIClientManager()
