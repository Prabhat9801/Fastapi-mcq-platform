"""
Smart MCQ Platform - Main Application Entry Point
FastAPI-based comprehensive exam preparation platform
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.core.exceptions import AppException
from create_admin import create_admin_user  # Import the admin creation function

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Smart MCQ Platform...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Create admin user
    try:
        logger.info("Checking/Creating admin user...")
        create_admin_user()
        logger.info("Admin user setup completed")
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        # Don't raise here - app can still run without admin user
    
    # Initialize vector database
    try:
        from app.services.vector_service import initialize_vector_db
        initialize_vector_db()
        logger.info("Vector database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize vector database: {e}")
        # Don't raise here - app can still run without vector db
    
    yield
    
    # Shutdown
    logger.info("Shutting down Smart MCQ Platform...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Comprehensive MCQ-based exam preparation platform with AI-powered question generation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", settings.HOST]
    )

# Include API routers
app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Smart MCQ Platform API",
        "docs": "/api/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable if available (for Render), otherwise fall back to settings
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Use 0.0.0.0 for deployment
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    )
