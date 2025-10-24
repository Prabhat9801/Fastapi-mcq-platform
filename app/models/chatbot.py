"""
Chatbot and RAG models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True)
    
    # Document details
    title = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, etc.
    file_size = Column(Integer, nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")
    processing_error = Column(Text, nullable=True)
    
    # Vector DB collection
    vector_collection_name = Column(String(100), nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatbotSession(Base):
    __tablename__ = "chatbot_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    # Session details
    session_token = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    query_count = Column(Integer, default=0)
    
    # Metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chatbot_sessions")
    messages = relationship("ChatbotMessage", back_populates="session", cascade="all, delete-orphan")


class ChatbotMessage(Base):
    __tablename__ = "chatbot_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chatbot_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Message details
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # Context used for response
    context_documents = Column(JSON, nullable=True)
    
    # Feedback
    is_helpful = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatbotSession", back_populates="messages")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Notification details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # test_reminder, subscription_expiry, announcement
    
    # Delivery
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Actions
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
