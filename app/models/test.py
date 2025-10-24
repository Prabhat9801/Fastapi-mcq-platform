"""
Test models - TestSeries, Test, Question
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TestType(str, enum.Enum):
    PRACTICE = "practice"
    LIVE = "live"
    MOCK = "mock"


class TestStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


class TestSeries(Base):
    __tablename__ = "test_series"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Visibility
    is_free = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="test_series")
    tests = relationship("Test", back_populates="test_series", cascade="all, delete-orphan")


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_series_id = Column(Integer, ForeignKey("test_series.id", ondelete="CASCADE"), nullable=False)
    
    # Basic info
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Test configuration
    test_type = Column(SQLEnum(TestType), default=TestType.PRACTICE)
    status = Column(SQLEnum(TestStatus), default=TestStatus.DRAFT)
    duration_minutes = Column(Integer, nullable=False)  # Total test duration
    time_per_question = Column(Integer, nullable=True)  # Optional per-question timer
    
    # Scheduling
    scheduled_start_time = Column(DateTime, nullable=True)
    scheduled_end_time = Column(DateTime, nullable=True)
    
    # Scoring
    total_marks = Column(Integer, default=0)
    passing_marks = Column(Integer, default=0)
    negative_marking_enabled = Column(Boolean, default=False)
    negative_marks_per_question = Column(Integer, default=0)
    
    # Access control
    is_free = Column(Boolean, default=False)
    max_attempts = Column(Integer, default=1)
    
    # Vector DB collection name for document-based questions
    vector_collection_name = Column(String(100), nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_series = relationship("TestSeries", back_populates="tests")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    attempts = relationship("TestAttempt", back_populates="test", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    
    # Question content
    question_text = Column(Text, nullable=False)
    question_image_url = Column(String(255), nullable=True)
    question_metadata = Column(JSON, nullable=True)  # For tables, charts, etc.
    
    # Question type and difficulty
    question_type = Column(SQLEnum(QuestionType), default=QuestionType.SINGLE_CHOICE)
    difficulty_level = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    
    # Options (stored as JSON array)
    options = Column(JSON, nullable=False)  # [{"text": "...", "image_url": "..."}, ...]
    
    # Correct answer(s)
    correct_answer_indices = Column(JSON, nullable=False)  # [0] for single, [0,2] for multiple
    
    # Explanation
    explanation = Column(Text, nullable=True)
    explanation_image_url = Column(String(255), nullable=True)
    
    # Scoring
    marks = Column(Integer, default=1)
    negative_marks = Column(Integer, default=0)
    
    # Ordering
    question_number = Column(Integer, nullable=False)
    
    # Tags for analytics
    topic_tags = Column(JSON, nullable=True)  # ["Indian Polity", "Fundamental Rights"]
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test = relationship("Test", back_populates="questions")
