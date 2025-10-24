"""Test-taking and attempt endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.test import Test, Question, TestStatus, TestSeries
from app.models.attempt import TestAttempt, AttemptStatus

logger = logging.getLogger(__name__)

router = APIRouter()

class StartTestResponse(BaseModel):
    attempt_id: int
    test: dict
    questions: List[dict]


@router.get("/")
async def get_available_tests(
    subject_id: Optional[int] = None,
    is_free: Optional[bool] = None, 
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all available (active) tests with optional filtering"""
    try:
        logger.info(f"Getting tests: subject_id={subject_id}, is_free={is_free}, skip={skip}, limit={limit}")
        
        # Base query for active tests
        query = db.query(Test).filter(Test.status == TestStatus.ACTIVE)
        
        # Apply subject filter through TestSeries join
        if subject_id is not None:
            query = query.join(TestSeries).filter(TestSeries.subject_id == subject_id)
            
        # Apply is_free filter
        if is_free is not None:
            query = query.filter(Test.is_free == is_free)
            
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        tests = query.offset(skip).limit(limit).all()
        
        logger.info(f"Found {total} total tests, returning {len(tests)} tests")
        
        # Build response - ALWAYS return a valid structure
        result = {
            "total": total,
            "tests": []
        }
        
        for test in tests:
            try:
                # Get test series info safely
                test_series = test.test_series
                if not test_series:
                    logger.warning(f"Test {test.id} has no test_series")
                    continue
                    
                # Count questions safely  
                question_count = db.query(Question).filter(Question.test_id == test.id).count()
                
                test_data = {
                    "id": test.id,
                    "title": test.name,
                    "description": test.description or "",
                    "test_series_id": test.test_series_id,
                    "test_series_name": test_series.name if test_series else "Unknown",
                    "subject_id": test_series.subject_id if test_series else None,
                    "question_count": question_count,
                    "duration_minutes": test.duration_minutes,
                    "total_marks": test.total_marks,
                    "is_free": test.is_free,
                    "test_type": test.test_type.value if test.test_type else "unknown",
                    "status": test.status.value if test.status else "unknown",
                    "created_at": test.created_at.isoformat() if test.created_at else None,
                    "updated_at": test.updated_at.isoformat() if test.updated_at else None
                }
                
                result["tests"].append(test_data)
                
            except Exception as e:
                logger.error(f"Error processing test {test.id}: {e}")
                continue
        
        logger.info(f"Returning response with {len(result['tests'])} tests")
        return result
        
    except Exception as e:
        logger.error(f"Error getting available tests: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tests: {str(e)}")


@router.get("/{test_id}")
async def get_test_details(
    test_id: int,
    db: Session = Depends(get_db)
):
    """Get test details (without questions/answers)"""
    test = db.query(Test).filter(Test.id == test_id, Test.status == TestStatus.ACTIVE).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found or not active")
    
    question_count = db.query(Question).filter(Question.test_id == test.id).count()
    
    return {
        "id": test.id,
        "title": test.name,
        "slug": test.slug,
        "description": getattr(test, 'description', ''),
        "duration": test.duration_minutes,
        "total_marks": test.total_marks,
        "question_count": question_count,
        "is_free": test.is_free,
        "test_type": test.test_type.value if hasattr(test.test_type, 'value') else test.test_type
    }


@router.post("/{test_id}/start", response_model=StartTestResponse)
async def start_test(test_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start a test attempt"""
    test = db.query(Test).filter(Test.id == test_id, Test.status == TestStatus.ACTIVE).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found or not active")
    
    # Get questions
    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.question_number).all()
    
    # Create attempt
    attempt = TestAttempt(
        user_id=current_user.id,
        test_id=test_id,
        total_questions=len(questions),
        status=AttemptStatus.IN_PROGRESS
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    # Return questions without correct answers
    questions_data = []
    for q in questions:
        questions_data.append({
            "id": q.id,
            "question_number": q.question_number,
            "question_text": q.question_text,
            "options": q.options,
            "marks": q.marks,
            "question_type": q.question_type
        })
    
    return {
        "attempt_id": attempt.id,
        "test": {
            "id": test.id,
            "name": test.name,
            "duration_minutes": test.duration_minutes,
            "total_marks": test.total_marks
        },
        "questions": questions_data
    }


@router.post("/attempts/{attempt_id}/submit")
async def submit_test(
    attempt_id: int,
    answers: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit test answers"""
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.status == AttemptStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Test already submitted")
    
    # Calculate score
    test = db.query(Test).filter(Test.id == attempt.test_id).first()
    questions = db.query(Question).filter(Question.test_id == test.id).all()
    
    score = 0
    correct_count = 0
    
    for question in questions:
        user_answer = answers.get(str(question.id))
        if user_answer and question.correct_answer_indices:
            if user_answer in question.correct_answer_indices:
                score += question.marks
                correct_count += 1
    
    # Update attempt
    attempt.status = AttemptStatus.COMPLETED
    attempt.completed_at = datetime.utcnow()
    attempt.answers = answers
    attempt.score = score
    attempt.correct_answers = correct_count
    
    db.commit()
    
    return {
        "message": "Test submitted successfully",
        "attempt_id": attempt_id,
        "score": score,
        "total_marks": test.total_marks,
        "correct_answers": correct_count,
        "total_questions": len(questions)
    }


@router.get("/attempts/{attempt_id}/results")
async def get_attempt_results(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed results of a test attempt"""
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.status != AttemptStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Test not yet completed")
    
    test = db.query(Test).filter(Test.id == attempt.test_id).first()
    questions = db.query(Question).filter(Question.test_id == test.id).all()
    
    # Build detailed results
    question_results = []
    for question in questions:
        user_answer = attempt.answers.get(str(question.id))
        is_correct = user_answer in question.correct_answer_indices if user_answer else False
        
        question_results.append({
            "question_number": question.question_number,
            "question_text": question.question_text,
            "options": question.options,
            "user_answer": user_answer,
            "correct_answer": question.correct_answer_indices[0] if question.correct_answer_indices else None,
            "is_correct": is_correct,
            "marks": question.marks if is_correct else 0,
            "explanation": question.explanation
        })
    
    return {
        "attempt_id": attempt.id,
        "test_name": test.name,
        "score": attempt.score,
        "total_marks": test.total_marks,
        "correct_answers": attempt.correct_answers,
        "total_questions": len(questions),
        "percentage": (attempt.score / test.total_marks * 100) if test.total_marks > 0 else 0,
        "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
        "question_results": question_results
    }
