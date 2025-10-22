"""
Admin API endpoints
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os
import secrets
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_admin
from app.models.user import User
from app.models.category import Category, Subject
from app.models.test import TestSeries, Test, Question, TestType, TestStatus, DifficultyLevel
from app.services.document_processor import document_processor
from app.services.vector_service import vector_service
from app.services.mcq_generator import mcq_generator
from app.services.fast_mcq_generator import fast_mcq_generator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon_url: Optional[str] = None


class SubjectCreate(BaseModel):
    category_id: int
    name: str
    slug: str
    description: Optional[str] = None


class TestSeriesCreate(BaseModel):
    subject_id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_free: bool = False


class TestGenerateResponse(BaseModel):
    test_id: int
    test_name: str
    total_questions: int
    questions: List[dict]
    message: str


@router.post("/categories", status_code=201)
async def create_category(
    category: CategoryCreate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new exam category"""
    
    # Check if slug exists
    existing = db.query(Category).filter(Category.slug == category.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category slug already exists")
    
    new_category = Category(
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon_url=category.icon_url,
        created_by=current_admin.id
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return {
        "message": "Category created successfully",
        "category": {
            "id": new_category.id,
            "name": new_category.name,
            "slug": new_category.slug
        }
    }


@router.get("/categories")
async def get_all_categories(
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all categories (admin view - includes inactive)"""
    categories = db.query(Category).all()
    
    result = []
    for category in categories:
        subjects_count = db.query(Subject).filter(Subject.category_id == category.id).count()
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


@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    category_data: CategoryCreate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if new slug conflicts with another category
    if category_data.slug != category.slug:
        existing = db.query(Category).filter(
            Category.slug == category_data.slug,
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category slug already exists")
    
    category.name = category_data.name
    category.slug = category_data.slug
    category.description = category_data.description
    category.icon_url = category_data.icon_url
    
    db.commit()
    db.refresh(category)
    
    return {
        "message": "Category updated successfully",
        "category": {
            "id": category.id,
            "name": category.name,
            "slug": category.slug
        }
    }


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has subjects
    subjects_count = db.query(Subject).filter(Subject.category_id == category_id).count()
    if subjects_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete category with {subjects_count} subjects. Delete subjects first."
        )
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}


@router.post("/subjects", status_code=201)
async def create_subject(
    subject: SubjectCreate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new subject under a category"""
    
    # Verify category exists
    category = db.query(Category).filter(Category.id == subject.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    new_subject = Subject(
        category_id=subject.category_id,
        name=subject.name,
        slug=subject.slug,
        description=subject.description,
        created_by=current_admin.id
    )
    
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    
    return {
        "message": "Subject created successfully",
        "subject": {
            "id": new_subject.id,
            "name": new_subject.name,
            "category_id": new_subject.category_id
        }
    }


@router.get("/subjects")
async def get_all_subjects(
    category_id: Optional[int] = None,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all subjects, optionally filtered by category"""
    query = db.query(Subject)
    
    if category_id:
        query = query.filter(Subject.category_id == category_id)
    
    subjects = query.all()
    
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


@router.put("/subjects/{subject_id}")
async def update_subject(
    subject_id: int,
    subject_data: SubjectCreate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update a subject"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Verify category exists
    category = db.query(Category).filter(Category.id == subject_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    subject.category_id = subject_data.category_id
    subject.name = subject_data.name
    subject.slug = subject_data.slug
    subject.description = subject_data.description
    
    db.commit()
    db.refresh(subject)
    
    return {
        "message": "Subject updated successfully",
        "subject": {
            "id": subject.id,
            "name": subject.name,
            "category_id": subject.category_id
        }
    }


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: int,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a subject"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    db.delete(subject)
    db.commit()
    
    return {"message": "Subject deleted successfully"}


# ========== TEST SERIES MANAGEMENT ==========

@router.post("/test-series", status_code=201)
async def create_test_series(
    test_series: TestSeriesCreate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new test series under a subject"""
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == test_series.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Check if slug exists
    existing = db.query(TestSeries).filter(TestSeries.slug == test_series.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Test series slug already exists")
    
    new_test_series = TestSeries(
        subject_id=test_series.subject_id,
        name=test_series.name,
        slug=test_series.slug,
        description=test_series.description,
        is_free=test_series.is_free,
        created_by=current_admin.id
    )
    
    db.add(new_test_series)
    db.commit()
    db.refresh(new_test_series)
    
    return {
        "message": "Test series created successfully",
        "test_series": {
            "id": new_test_series.id,
            "name": new_test_series.name,
            "slug": new_test_series.slug,
            "subject_id": new_test_series.subject_id
        }
    }


@router.get("/test-series")
async def get_all_test_series(
    subject_id: Optional[int] = None,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all test series, optionally filtered by subject"""
    query = db.query(TestSeries)
    
    if subject_id:
        query = query.filter(TestSeries.subject_id == subject_id)
    
    test_series = query.all()
    
    result = []
    for ts in test_series:
        tests_count = db.query(Test).filter(Test.test_series_id == ts.id).count()
        result.append({
            "id": ts.id,
            "subject_id": ts.subject_id,
            "name": ts.name,
            "slug": ts.slug,
            "description": ts.description,
            "is_free": ts.is_free,
            "is_active": ts.is_active,
            "tests_count": tests_count,
            "created_at": ts.created_at.isoformat() if ts.created_at else None
        })
    
    return result


@router.put("/test-series/{test_series_id}")
async def update_test_series(
    test_series_id: int,
    test_series_data: TestSeriesCreate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update a test series"""
    test_series = db.query(TestSeries).filter(TestSeries.id == test_series_id).first()
    if not test_series:
        raise HTTPException(status_code=404, detail="Test series not found")
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == test_series_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Check if new slug conflicts
    if test_series_data.slug != test_series.slug:
        existing = db.query(TestSeries).filter(
            TestSeries.slug == test_series_data.slug,
            TestSeries.id != test_series_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Test series slug already exists")
    
    test_series.subject_id = test_series_data.subject_id
    test_series.name = test_series_data.name
    test_series.slug = test_series_data.slug
    test_series.description = test_series_data.description
    test_series.is_free = test_series_data.is_free
    
    db.commit()
    db.refresh(test_series)
    
    return {
        "message": "Test series updated successfully",
        "test_series": {
            "id": test_series.id,
            "name": test_series.name,
            "slug": test_series.slug
        }
    }


@router.delete("/test-series/{test_series_id}")
async def delete_test_series(
    test_series_id: int,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a test series"""
    test_series = db.query(TestSeries).filter(TestSeries.id == test_series_id).first()
    if not test_series:
        raise HTTPException(status_code=404, detail="Test series not found")
    
    # Check if test series has tests
    tests_count = db.query(Test).filter(Test.test_series_id == test_series_id).count()
    if tests_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete test series with {tests_count} tests. Delete tests first."
        )
    
    db.delete(test_series)
    db.commit()
    
    return {"message": "Test series deleted successfully"}


# ========== TEST GENERATION ==========

@router.post("/tests/generate", response_model=TestGenerateResponse)
async def generate_test_from_document(
    file: UploadFile = File(...),
    test_series_id: int = Form(...),
    test_name: str = Form(...),
    num_questions: int = Form(10),
    difficulty_level: str = Form("medium"),
    topic_scope: str = Form("comprehensive"),
    duration_minutes: int = Form(60),
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Generate a test with MCQs from uploaded document
    Supports both scanned and digital documents
    """
    
    # Verify test series exists
    test_series = db.query(TestSeries).filter(TestSeries.id == test_series_id).first()
    if not test_series:
        raise HTTPException(status_code=404, detail="Test series not found")
    
    # Save uploaded file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{secrets.token_hex(8)}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    try:
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        doc_result = document_processor.process_document(
            file_path,
            extract_images=True,
            extract_tables=True
        )
        
        # Create vector collection
        collection_name = f"test_{secrets.token_hex(8)}"
        vector_service.create_collection(collection_name)
        
        # Chunk and store text
        chunks = document_processor.chunk_text_intelligently(doc_result["text"])
        vector_service.add_documents(
            collection_name=collection_name,
            documents=chunks
        )
        
        # Generate MCQs
        questions = mcq_generator.generate_from_document(
            collection_name=collection_name,
            query_scope=topic_scope,
            num_questions=num_questions,
            difficulty_level=difficulty_level
        )
        
        # Create test
        new_test = Test(
            test_series_id=test_series_id,
            name=test_name,
            slug=test_name.lower().replace(" ", "-"),
            test_type=TestType.PRACTICE,
            status=TestStatus.DRAFT,
            duration_minutes=duration_minutes,
            total_marks=len(questions),
            vector_collection_name=collection_name,
            created_by=current_admin.id
        )
        
        db.add(new_test)
        db.flush()
        
        # Create questions
        for i, q_data in enumerate(questions):
            question = Question(
                test_id=new_test.id,
                question_text=q_data["question"],
                question_type=q_data.get("question_type", "single_choice"),
                difficulty_level=DifficultyLevel(q_data.get("difficulty_level", "medium")),
                options=q_data["options"],
                correct_answer_indices=[q_data["correct_answer_index"]],
                explanation=q_data.get("explanation", ""),
                marks=q_data.get("marks", 1),
                question_number=i + 1,
                topic_tags=q_data.get("topic_tags", [])
            )
            db.add(question)
        
        db.commit()
        db.refresh(new_test)
        
        return {
            "test_id": new_test.id,
            "test_name": new_test.name,
            "total_questions": len(questions),
            "questions": questions,
            "message": f"Successfully generated {len(questions)} questions"
        }
        
    except Exception as e:
        db.rollback()
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error generating test: {str(e)}")
    finally:
        # Cleanup uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@router.post("/tests/generate-fast", response_model=TestGenerateResponse)
async def generate_test_fast(
    file: UploadFile = File(...),
    test_series_id: int = Form(...),
    test_name: str = Form(...),
    num_questions: int = Form(10),
    difficulty_level: str = Form("medium"),
    topic_scope: str = Form("comprehensive"),
    duration_minutes: int = Form(60),
    specific_pages: Optional[str] = Form(None),
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    ⚡ FAST test generation using CLIP + ChromaDB + Gemini
    Based on optimized app.py implementation
    
    - No OCR required (digital PDFs only)
    - 3-5x faster than standard generation
    - Uses CLIP embeddings + RAG approach
    """
    
    # Verify test series exists
    test_series = db.query(TestSeries).filter(TestSeries.id == test_series_id).first()
    if not test_series:
        raise HTTPException(status_code=404, detail="Test series not found")
    
    # Save uploaded file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    
    if file_extension.lower() != '.pdf':
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    unique_filename = f"{secrets.token_hex(8)}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    collection_name = None
    
    try:
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing PDF: {file.filename}")
        
        # Generate test using fast pipeline
        questions, collection_name = fast_mcq_generator.generate_test_from_pdf(
            pdf_path=file_path,
            num_questions=num_questions,
            difficulty_level=difficulty_level,
            topic_scope=topic_scope,
            specific_pages=specific_pages
        )
        
        logger.info(f"Generated {len(questions)} questions")
        
        # Create test
        new_test = Test(
            test_series_id=test_series_id,
            name=test_name,
            slug=test_name.lower().replace(" ", "-").replace("_", "-"),
            test_type=TestType.PRACTICE,
            status=TestStatus.ACTIVE,
            duration_minutes=duration_minutes,
            total_marks=len(questions),
            vector_collection_name=collection_name,
            created_by=current_admin.id
        )
        
        db.add(new_test)
        db.flush()
        
        # Create questions
        for i, q_data in enumerate(questions):
            question = Question(
                test_id=new_test.id,
                question_text=q_data["question"],
                question_type="single_choice",
                difficulty_level=DifficultyLevel(difficulty_level.lower()),
                options=q_data["options"],
                correct_answer_indices=[q_data["correct_answer_index"]],
                explanation=q_data.get("explanation", ""),
                marks=1,
                question_number=i + 1,
                topic_tags=[]
            )
            db.add(question)
        
        db.commit()
        db.refresh(new_test)
        
        logger.info(f"✅ Test created successfully: {new_test.id}")
        
        return {
            "test_id": new_test.id,
            "test_name": new_test.name,
            "total_questions": len(questions),
            "questions": questions,
            "message": f"⚡ Fast generation: Created {len(questions)} questions in seconds!"
        }
        
    except Exception as e:
        db.rollback()
        
        # Cleanup vector collection
        if collection_name:
            try:
                fast_mcq_generator.delete_collection(collection_name)
            except:
                pass
        
        logger.error(f"Fast test generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating test: {str(e)}")
        
    finally:
        # Cleanup uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@router.get("/tests")
async def get_all_tests(
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all tests with question counts"""
    tests = db.query(Test).all()
    
    result = []
    for test in tests:
        question_count = db.query(Question).filter(Question.test_id == test.id).count()
        result.append({
            "id": test.id,
            "name": test.name,
            "test_type": test.test_type.value,
            "status": test.status.value,
            "duration_minutes": test.duration_minutes,
            "total_marks": test.total_marks,
            "question_count": question_count,
            "created_at": test.created_at
        })
    
    return {"tests": result}


@router.put("/tests/{test_id}/publish")
async def publish_test(
    test_id: int,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Publish a test (make it active)"""
    
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    test.status = TestStatus.ACTIVE
    db.commit()
    
    return {"message": "Test published successfully"}


@router.delete("/tests/{test_id}")
async def delete_test(
    test_id: int,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a test and its questions"""
    
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Delete vector collection
    if test.vector_collection_name:
        try:
            vector_service.delete_collection(test.vector_collection_name)
        except:
            pass
    
    # Delete test (questions will cascade delete)
    db.delete(test)
    db.commit()
    
    return {"message": "Test deleted successfully"}


@router.put("/tests/{test_id}")
async def update_test(
    test_id: int,
    test_data: dict,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update test details"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Update fields
    if "name" in test_data:
        test.name = test_data["name"]
    if "duration_minutes" in test_data:
        test.duration_minutes = test_data["duration_minutes"]
    if "total_marks" in test_data:
        test.total_marks = test_data["total_marks"]
    if "is_free" in test_data:
        test.is_free = test_data["is_free"]
    
    db.commit()
    db.refresh(test)
    
    return {"message": "Test updated successfully", "test": {"id": test.id, "name": test.name}}


# User Management Endpoints
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get all users with filters"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        query = query.filter(User.status == status)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "status": user.status.value if hasattr(user.status, 'value') else user.status,
            "total_points": user.total_points,
            "current_streak": user.current_streak,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })
    
    return {"total": total, "users": result}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update user details (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_data.full_name:
        user.full_name = user_data.full_name
    if user_data.email:
        # Check email uniqueness
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_data.email
    if user_data.role:
        user.role = user_data.role
    if user_data.status:
        user.status = user_data.status
    
    db.commit()
    db.refresh(user)
    
    return {"message": "User updated successfully", "user": {"id": user.id, "username": user.username}}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}
