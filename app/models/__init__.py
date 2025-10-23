"""
Models package initialization
Import all models here for easy access
"""

from app.models.user import User, UserRole, UserStatus
from app.models.category import Category, Subject
from app.models.test import TestSeries, Test, Question, TestType, TestStatus, DifficultyLevel, QuestionType
from app.models.subscription import SubscriptionPlan, UserSubscription, Payment, PlanDuration, SubscriptionStatus, PaymentStatus, PaymentMethod
from app.models.attempt import TestAttempt, AttemptStatus
from app.models.gamification import Badge, UserBadge, Referral
from app.models.chatbot import Document, ChatbotSession, ChatbotMessage, Notification

__all__ = [
    "User", "UserRole", "UserStatus",
    "Category", "Subject",
    "TestSeries", "Test", "Question", "TestType", "TestStatus", "DifficultyLevel", "QuestionType",
    "SubscriptionPlan", "UserSubscription", "Payment", "PlanDuration", "SubscriptionStatus", "PaymentStatus", "PaymentMethod",
    "TestAttempt", "AttemptStatus",
    "Badge", "UserBadge", "Referral",
    "Document", "ChatbotSession", "ChatbotMessage", "Notification"
]
