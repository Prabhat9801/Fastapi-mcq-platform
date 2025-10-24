"""
Main API router - aggregates all API endpoints
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.categories import router as categories_router
from app.api.v1.tests import router as tests_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(categories_router, prefix="/categories", tags=["Categories"])
api_router.include_router(tests_router, prefix="/tests", tags=["Tests"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["Chatbot"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
