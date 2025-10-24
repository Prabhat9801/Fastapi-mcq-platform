"""
Smart MCQ Platform - Main Application Entry Point
FastAPI-based comprehensive exam preparation platform
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.database import SessionLocal, engine
from app.models.user import User, UserRole, UserStatus, Base
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.api.v1 import api_router
from app.core.exceptions import AppException

# Import all models to ensure they're registered with Base
from app.models import user, test, attempt, category, subscription, chat, chatbot, gamification

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_database_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {str(e)}")
        raise


def create_admin_user():
    """Create admin user if not exists"""
    db = SessionLocal()
    
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("✅ Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")
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
        
        print("🎉 Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Password: admin123")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print("\n⚠️  Please change the password after first login!")
        
    except IntegrityError as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        print("Admin user might already exist with different details.")
    except Exception as e:
        db.rollback()
        print(f"❌ Unexpected error: {str(e)}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    print("=" * 50)
    print("Starting MCQ Platform Application")
    print("=" * 50)
    
    # Create database tables first
    create_database_tables()
    
    # Then create admin user
    print("Creating Admin User for MCQ Platform")
    print("=" * 50)
    create_admin_user()
    print("=" * 50)
    print("Application startup complete!")
    
    yield
    
    # Shutdown events
    print("Shutting down MCQ Platform...")


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
