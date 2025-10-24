"""
Subscription and Payment models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class PlanDuration(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    MANUAL = "manual"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    
    # Plan details
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    duration = Column(SQLEnum(PlanDuration), nullable=False)
    duration_days = Column(Integer, nullable=False)
    
    # Pricing
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2), nullable=True)
    discount_percentage = Column(Integer, default=0)
    
    # Features (JSON array)
    features = Column(String(1000), nullable=True)  # JSON string
    
    # Limits
    max_test_attempts = Column(Integer, default=-1)  # -1 = unlimited
    chatbot_query_limit = Column(Integer, default=100)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="subscription_plans")
    user_subscriptions = relationship("UserSubscription", back_populates="plan", cascade="all, delete-orphan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)
    
    # Subscription details
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Usage tracking
    test_attempts_used = Column(Integer, default=0)
    chatbot_queries_used = Column(Integer, default=0)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    category = relationship("Category", back_populates="user_subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")
    payment = relationship("Payment", back_populates="subscription", uselist=False)


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("user_subscriptions.id", ondelete="SET NULL"), nullable=True)
    
    # Payment details
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Gateway transaction details
    transaction_id = Column(String(100), unique=True, nullable=True)
    gateway_response = Column(String(1000), nullable=True)  # JSON string
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("UserSubscription", back_populates="payment")
