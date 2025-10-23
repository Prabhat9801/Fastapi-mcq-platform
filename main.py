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
from app.core.database import engine, Base, SessionLocal
from app.api.v1 import api_router
from app.core.exceptions import AppException
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_admin_user():
    """Create default admin user if not exists"""
    db = SessionLocal()
    
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            logger.info("✅ Admin user already exists")
            logger.info(f"   Username: {existing_admin.username}")
            logger.info(f"   Email: {existing_admin.email}")
            logger.info(f"   Role: {existing_admin.role}")
            return
        
        admin_user = User(
            email="admin@mcq.com",
            username="admin",
            full_name="Administrator",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("🎉 Admin user created successfully!")
        logger.info(f"   Username: {admin_user.username}")
        logger.info(f"   Password: admin123")
        logger.info(f"   Email: {admin_user.email}")
        logger.info(f"   Role: {admin_user.role}")
        logger.warning("⚠️  Please change the password after first login!")
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"❌ Database integrity error during admin creation: {str(e)}")
        logger.info("Admin user might already exist with different details.")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Unexpected error during admin creation: {str(e)}")
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Smart MCQ Platform...")
    
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Create admin user
        logger.info("Checking/Creating admin user...")
        create_admin_user()
        
        # Initialize vector database
        from app.services.vector_service import initialize_vector_db
        logger.info("Initializing vector database...")
        initialize_vector_db()
        logger.info("Vector database initialized")
        
        logger.info("✅ Smart MCQ Platform startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        # Continue startup even if non-critical components fail
        logger.warning("Continuing with startup despite errors...")
    
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
