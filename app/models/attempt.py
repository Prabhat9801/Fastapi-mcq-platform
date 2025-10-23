"""
Test Attempt and Analytics models
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    
    # Attempt details
    status = Column(SQLEnum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)
    attempt_number = Column(Integer, default=1)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    
    # Answers (JSON array of user responses)
    answers = Column(JSON, nullable=True)  # [{"question_id": 1, "selected_indices": [0], "time_taken": 30}, ...]
    
    # Scoring
    total_questions = Column(Integer, default=0)
    attempted_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    unanswered = Column(Integer, default=0)
    
    score = Column(Integer, default=0)
    total_marks = Column(Integer, default=0)
    percentage = Column(Integer, default=0)
    
    # Analytics
    accuracy = Column(Integer, default=0)  # Percentage
    rank = Column(Integer, nullable=True)
    percentile = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="test_attempts")
    test = relationship("Test", back_populates="attempts")
