"""
Main FastAPI application for the debate bot.
Implements the chat API with automatic Swagger documentation.
"""

import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from app.services import conversation_service
from app.middleware import RateLimitMiddleware, ErrorHandlerMiddleware, ConversationNotFoundError, AIServiceError
from app import __version__

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Debate Bot API",
    description="A conversational AI that maintains controversial positions in debates",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request format"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Chat with the debate bot",
    description="""
    Send a message to the debate bot and receive a controversial response.
    
    - For new conversations: send message without conversation_id
    - For existing conversations: include the conversation_id
    - Only 'conversation_id' and 'message' attributes are allowed
    - Messages are limited to 5000 characters
    - Rate limited to 100 requests per minute per IP
    """
)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for debating with the bot.
    
    The bot will:
    1. Analyze your message to determine the topic (if new conversation)
    2. Assign itself a controversial position to defend
    3. Generate persuasive responses that maintain its stance
    4. Continue the debate while staying consistent with its position
    """
    try:
        if request.conversation_id is None or request.conversation_id == "":
            # Start new conversation
            logger.info("Starting new conversation")
            result = conversation_service.start_new_conversation(request.message)
        else:
            # Continue existing conversation
            logger.info(f"Continuing conversation: {request.conversation_id}")
            result = conversation_service.continue_conversation(
                request.conversation_id, 
                request.message
            )
        
        return ChatResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConversationNotFoundError:
        logger.warning(f"Conversation not found: {request.conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {request.conversation_id} not found"
        )
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running and healthy"
)
async def health():
    """
    Health check endpoint.
    
    Returns the current status of the API service.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=__version__
    )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "Debate Bot API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting Debate Bot API v{__version__}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Rate limit: {settings.rate_limit_per_minute} requests/minute")
    
    # Validate OpenAI API key on startup
    from app.services.retry_service import openai_client
    if not openai_client.validate_api_key():
        logger.error("OpenAI API key validation failed!")
    else:
        logger.info("OpenAI API key validated successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Debate Bot API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
