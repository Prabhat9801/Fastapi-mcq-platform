"""User profile and dashboard endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash
from app.models.user import User
from app.models.attempt import TestAttempt, AttemptStatus

router = APIRouter()


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "status": current_user.status.value if hasattr(current_user.status, 'value') else current_user.status,
        "total_points": current_user.total_points,
        "current_streak": current_user.current_streak,
        "level": current_user.level if hasattr(current_user, 'level') else 1,
        "referral_code": current_user.referral_code,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.put("/me")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    if profile_data.full_name:
        current_user.full_name = profile_data.full_name
    
    if profile_data.phone:
        current_user.phone = profile_data.phone
    
    if profile_data.email:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == profile_data.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = profile_data.email
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully"}


@router.get("/me/attempts")
async def get_test_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's test attempt history"""
    attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.status == AttemptStatus.COMPLETED
    ).order_by(TestAttempt.completed_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for attempt in attempts:
        from app.models.test import Test
        test = db.query(Test).filter(Test.id == attempt.test_id).first()
        
        result.append({
            "attempt_id": attempt.id,
            "test_id": attempt.test_id,
            "test_name": test.name if test else "Unknown Test",
            "score": attempt.score,
            "total_marks": test.total_marks if test else 0,
            "percentage": (attempt.score / test.total_marks * 100) if test and test.total_marks > 0 else 0,
            "correct_answers": attempt.correct_answers,
            "total_questions": attempt.total_questions,
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
        })
    
    return {"attempts": result}


@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    # Total attempts
    total_attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.status == AttemptStatus.COMPLETED
    ).count()
    
    # Average score
    attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.status == AttemptStatus.COMPLETED
    ).all()
    
    avg_percentage = 0
    if attempts:
        from app.models.test import Test
        total_percentage = 0
        valid_attempts = 0
        
        for attempt in attempts:
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            if test and test.total_marks > 0:
                total_percentage += (attempt.score / test.total_marks * 100)
                valid_attempts += 1
        
        if valid_attempts > 0:
            avg_percentage = total_percentage / valid_attempts
    
    return {
        "total_points": current_user.total_points,
        "current_streak": current_user.current_streak,
        "level": current_user.level if hasattr(current_user, 'level') else 1,
        "total_tests_taken": total_attempts,
        "average_score": round(avg_percentage, 2)
    }


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user dashboard data"""
    return {"message": "Dashboard endpoint - to be implemented"}


@router.get("/history")
async def get_test_history_legacy(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user test history (legacy endpoint)"""
    return await get_test_history(current_user=current_user, db=db)
