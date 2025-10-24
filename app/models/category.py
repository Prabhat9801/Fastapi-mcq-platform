"""
Category model - represents exam categories like UPSC, SSC, Banking, etc.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(255), nullable=True)
    banner_url = Column(String(255), nullable=True)
    
    # Display order
    display_order = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subjects = relationship("Subject", back_populates="category", cascade="all, delete-orphan")
    subscription_plans = relationship("SubscriptionPlan", back_populates="category", cascade="all, delete-orphan")
    user_subscriptions = relationship("UserSubscription", back_populates="category", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(255), nullable=True)
    
    # Display order
    display_order = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="subjects")
    test_series = relationship("TestSeries", back_populates="subject", cascade="all, delete-orphan")
