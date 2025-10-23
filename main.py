"""
Smart MCQ Platform - Main Application Entry Point
FastAPI-based comprehensive exam preparation platform
"""

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
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Create admin user automatically
    try:
        from create_admin import create_admin_user
        create_admin_user()
        logger.info("Admin user creation process completed")
    except Exception as e:
        logger.warning(f"Admin user creation failed: {str(e)}")
    
    # Initialize vector database
    from app.services.vector_service import initialize_vector_db
    initialize_vector_db()
    logger.info("Vector database initialized")
    
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
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
