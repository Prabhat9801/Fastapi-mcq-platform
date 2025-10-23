"""
Smart MCQ Platform - Minimal Render-Compatible Version
"""

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app that always works
app = FastAPI(
    title="Smart MCQ Platform",
    description="MCQ Platform API",
    version="1.0.0"
)

# Minimal CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Essential endpoints that Render needs to detect
@app.get("/")
async def root():
    """Root endpoint - must respond for Render to detect service"""
    port = os.environ.get("PORT", "unknown")
    logger.info(f"Root endpoint accessed - PORT: {port}")
    return {
        "message": "Smart MCQ Platform API",
        "status": "running",
        "port": port,
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    port = os.environ.get("PORT", "unknown")
    logger.info(f"Health check - PORT: {port}")
    return {
        "status": "healthy",
        "port": port
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

# Try to load full config and features, but don't fail if they don't work
try:
    from app.core.config import settings
    logger.info(f"✅ Settings loaded - PORT from config: {settings.PORT}")
    
    # Update app metadata
    app.title = settings.APP_NAME
    
    # Try to include API routes
    try:
        from app.api.v1 import api_router
        app.include_router(api_router, prefix="/api/v1")
        logger.info("✅ API routes included")
    except Exception as e:
        logger.warning(f"⚠️  API routes not available: {e}")
        
        # Add fallback API endpoint
        @app.get("/api/v1/status")
        async def api_status():
            return {"message": "API loading...", "error": str(e)}
    
    # Try to set up database and admin user (async startup)
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup events with error handling"""
        try:
            logger.info("Starting application...")
            
            # Database setup
            try:
                from app.core.database import engine, Base
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Database tables created")
            except Exception as e:
                logger.warning(f"⚠️  Database setup failed: {e}")
            
            # Admin user creation
            try:
                from create_admin import create_admin_user
                await create_admin_user()
                logger.info("✅ Admin user setup completed")
            except Exception as e:
                logger.warning(f"⚠️  Admin user creation failed: {e}")
                
            logger.info("🚀 Application startup completed")
        except Exception as e:
            logger.error(f"❌ Startup error: {e}")
            # Continue anyway - don't crash the server
        
        yield
        
        logger.info("🛑 Application shutting down...")
    
    # Apply lifespan to app
    app.router.lifespan_context = lifespan
    
except Exception as e:
    logger.warning(f"⚠️  Full config not available, running in minimal mode: {e}")

# Log startup info
logger.info(f"📋 FastAPI app created - PORT env var: {os.environ.get('PORT', 'not set')}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
