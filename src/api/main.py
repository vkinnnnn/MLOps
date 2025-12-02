"""
FastAPI application for the DocAI EXTRACTOR platform.
Includes performance optimizations with caching and connection pooling.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from contextlib import asynccontextmanager
import asyncio

from src.api.routes import router
from src.api.advanced_routes import router as advanced_router
from src.api.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from src.api.cache_manager import get_cache_manager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)


async def cleanup_cache_periodically():
    """Background task to cleanup expired cache entries periodically."""
    cache = get_cache_manager()
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        cache.cleanup_expired()
        logger.info("Cache cleanup completed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting DocAI EXTRACTOR API")
    
    # Start background cache cleanup task
    cleanup_task = asyncio.create_task(cleanup_cache_periodically())
    
    yield
    
    # Cleanup on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    logger.info("Shutting down DocAI EXTRACTOR API")


app = FastAPI(
    title="DocAI EXTRACTOR API",
    description="REST API for extracting and comparing financial and student loan document data with performance optimizations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(advanced_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "DocAI EXTRACTOR API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "features": [
            "Response caching for improved performance",
            "Database connection pooling",
            "Parallel OCR processing for multi-page documents",
            "Optimized database queries with indexes",
            "Multilingual translation (10+ languages)",
            "RAG-based financial chatbot",
            "AI-powered loan comparison",
            "Financial literacy education"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    cache = get_cache_manager()
    cache_stats = cache.get_stats()
    
    return {
        "status": "healthy",
        "cache": {
            "enabled": True,
            "size": cache_stats['size'],
            "hit_rate": cache_stats['hit_rate']
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
