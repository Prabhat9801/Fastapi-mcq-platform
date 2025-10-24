"""Subscription and payment endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/plans")
async def get_subscription_plans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all subscription plans"""
    return {"message": "Subscription plans endpoint - to be implemented"}

@router.post("/purchase")
async def purchase_subscription(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Purchase a subscription plan"""
    return {"message": "Purchase endpoint - to be implemented"}
