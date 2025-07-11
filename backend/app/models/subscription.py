"""
Subscription and Payment models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    FAMILY = "family"


class PaymentStatus(str, enum.Enum):
    """Payment status types"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Subscription(Base):
    """User subscription model"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Subscription details
    plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, cancelled, expired
    
    # Stripe information
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_price_id = Column(String(255))
    
    # Subscription period
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    # Billing
    next_billing_date = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Features and limits
    features = Column(JSON, default={})  # JSON object with feature flags
    usage_limits = Column(JSON, default={})  # JSON object with usage limits
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    # Payment details
    amount = Column(Float, nullable=False)  # Amount in cents
    currency = Column(String(3), default="USD", nullable=False)
    description = Column(String(500))
    
    # Stripe information
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_charge_id = Column(String(255), unique=True, index=True)
    stripe_invoice_id = Column(String(255), index=True)
    payment_method_type = Column(String(50))  # card, bank_transfer, etc.
    
    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    failure_reason = Column(String(500))
    
    # Metadata
    metadata = Column(JSON, default={})  # Additional payment metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class UsageRecord(Base):
    """Track usage for metered billing"""
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    
    # Usage details
    metric_name = Column(String(100), nullable=False)  # ai_requests, storage_gb, etc.
    quantity = Column(Float, nullable=False)
    unit = Column(String(50))  # requests, GB, hours, etc.
    
    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")


class PlanFeature(Base):
    """Define features for each plan"""
    __tablename__ = "plan_features"
    
    id = Column(Integer, primary_key=True, index=True)
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False)
    
    # Feature details
    feature_name = Column(String(100), nullable=False)
    feature_key = Column(String(100), nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    
    # Limits (null means unlimited)
    limit_value = Column(Integer, nullable=True)
    limit_unit = Column(String(50))  # per_month, per_day, total, etc.
    
    # Display information
    display_name = Column(String(200))
    description = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)