"""
Rate limiting middleware for the debate bot API.
Implements sliding window rate limiting with 100 requests per minute per IP.
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store timestamps of requests per IP
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_ip: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed for given IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] <= current_time - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(current_time)
            return True, None
        else:
            # Calculate retry after time (when oldest request expires)
            oldest_request = client_requests[0]
            retry_after = int(oldest_request + self.window_seconds - current_time) + 1
            return False, retry_after
    
    def cleanup_old_entries(self):
        """Clean up old entries to prevent memory leaks."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        # Remove IPs with no recent requests
        ips_to_remove = []
        for ip, requests in self.requests.items():
            while requests and requests[0] <= cutoff_time:
                requests.popleft()
            if not requests:
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self.requests[ip]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter(
            max_requests=settings.rate_limit_per_minute,
            window_seconds=60
        )
        self.excluded_paths = {"/docs", "/openapi.json", "/redoc", "/health"}
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter."""
        
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.is_allowed(client_ip)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {settings.rate_limit_per_minute} per minute",
                    "retry_after": retry_after,
                    "postman_collection": settings.postman_collection_url,
                    "swagger_docs": settings.swagger_docs_url
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Proceed with request
        response = await call_next(request)
        
        # Periodic cleanup (every 100th request)
        if time.time() % 100 < 1:
            self.rate_limiter.cleanup_old_entries()
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check for forwarded headers (for reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)
