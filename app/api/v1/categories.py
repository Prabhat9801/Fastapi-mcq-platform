"""User-facing category endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.category import Category, Subject

router = APIRouter()

@router.get("/")
async def get_categories(db: Session = Depends(get_db)):
    """Get all active categories (public endpoint - no authentication required)"""
    categories = db.query(Category).filter(Category.is_active == True).all()
    
    # Add subjects count to each category
    result = []
    for category in categories:
        subjects_count = db.query(Subject).filter(
            Subject.category_id == category.id,
            Subject.is_active == True
        ).count()
        
        result.append({
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "icon": category.icon_url,
            "is_active": category.is_active,
            "subjects_count": subjects_count,
            "created_at": category.created_at.isoformat() if category.created_at else None
        })
    
    return result

@router.get("/{category_id}/subjects")
async def get_category_subjects(category_id: int, db: Session = Depends(get_db)):
    """Get all subjects under a category (public endpoint)"""
    subjects = db.query(Subject).filter(Subject.category_id == category_id, Subject.is_active == True).all()
    
    result = []
    for subject in subjects:
        result.append({
            "id": subject.id,
            "category_id": subject.category_id,
            "name": subject.name,
            "slug": subject.slug,
            "description": subject.description,
            "is_active": subject.is_active,
            "created_at": subject.created_at.isoformat() if subject.created_at else None
        })
    
    return result
