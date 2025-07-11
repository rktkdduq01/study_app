"""
Payment service for handling Stripe payments and subscriptions
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import stripe
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import settings
from app.core.logger import get_logger
from app.models.user import User
from app.models.subscription import (
    Subscription, Payment, UsageRecord, PlanFeature,
    SubscriptionPlan, PaymentStatus
)
from app.core.exceptions import AppException

logger = get_logger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_API_KEY


class PaymentService:
    """Service for handling payments and subscriptions"""
    
    # Plan configuration
    PLANS = {
        SubscriptionPlan.FREE: {
            "name": "Free Plan",
            "price": 0,
            "features": {
                "ai_requests_per_month": 50,
                "practice_questions_per_day": 10,
                "learning_paths": 1,
                "storage_gb": 1,
                "multiplayer": False,
                "priority_support": False
            }
        },
        SubscriptionPlan.BASIC: {
            "name": "Basic Plan",
            "price": 999,  # $9.99 in cents
            "stripe_price_id": settings.STRIPE_PRICE_ID_BASIC,
            "features": {
                "ai_requests_per_month": 500,
                "practice_questions_per_day": 50,
                "learning_paths": 5,
                "storage_gb": 5,
                "multiplayer": True,
                "priority_support": False
            }
        },
        SubscriptionPlan.PREMIUM: {
            "name": "Premium Plan",
            "price": 1999,  # $19.99 in cents
            "stripe_price_id": settings.STRIPE_PRICE_ID_PREMIUM,
            "features": {
                "ai_requests_per_month": 2000,
                "practice_questions_per_day": -1,  # Unlimited
                "learning_paths": -1,  # Unlimited
                "storage_gb": 20,
                "multiplayer": True,
                "priority_support": True,
                "advanced_analytics": True,
                "custom_content": True
            }
        },
        SubscriptionPlan.FAMILY: {
            "name": "Family Plan",
            "price": 2999,  # $29.99 in cents
            "stripe_price_id": settings.STRIPE_PRICE_ID_FAMILY,
            "features": {
                "ai_requests_per_month": 5000,
                "practice_questions_per_day": -1,  # Unlimited
                "learning_paths": -1,  # Unlimited
                "storage_gb": 50,
                "multiplayer": True,
                "priority_support": True,
                "advanced_analytics": True,
                "custom_content": True,
                "family_accounts": 5,
                "parental_controls": True
            }
        }
    }
    
    async def create_customer(self, user: User, db: Session) -> str:
        """Create Stripe customer for user"""
        try:
            # Check if customer already exists
            subscription = db.query(Subscription).filter_by(user_id=user.id).first()
            if subscription and subscription.stripe_customer_id:
                return subscription.stripe_customer_id
            
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "user_id": str(user.id),
                    "username": user.username
                }
            )
            
            # Create or update subscription record
            if not subscription:
                subscription = Subscription(
                    user_id=user.id,
                    plan=SubscriptionPlan.FREE,
                    status="active",
                    features=self.PLANS[SubscriptionPlan.FREE]["features"],
                    usage_limits=self.PLANS[SubscriptionPlan.FREE]["features"]
                )
                db.add(subscription)
            
            subscription.stripe_customer_id = customer.id
            db.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            raise AppException(
                message="Failed to create customer account",
                status_code=500,
                error_code="STRIPE_ERROR"
            )
    
    async def create_subscription(
        self,
        user: User,
        plan: SubscriptionPlan,
        payment_method_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Create a new subscription"""
        try:
            # Validate plan
            if plan not in self.PLANS or plan == SubscriptionPlan.FREE:
                raise AppException(
                    message="Invalid subscription plan",
                    status_code=400,
                    error_code="INVALID_PLAN"
                )
            
            # Get or create customer
            customer_id = await self.create_customer(user, db)
            
            # Attach payment method to customer
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            # Create subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": self.PLANS[plan]["stripe_price_id"]}],
                payment_settings={
                    "payment_method_types": ["card"],
                    "save_default_payment_method": "on_subscription"
                },
                expand=["latest_invoice.payment_intent"],
                metadata={
                    "user_id": str(user.id),
                    "plan": plan.value
                }
            )
            
            # Update database subscription
            subscription = db.query(Subscription).filter_by(user_id=user.id).first()
            subscription.plan = plan
            subscription.status = stripe_subscription.status
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.stripe_price_id = self.PLANS[plan]["stripe_price_id"]
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end
            )
            subscription.features = self.PLANS[plan]["features"]
            subscription.usage_limits = self.PLANS[plan]["features"]
            
            db.commit()
            
            logger.info(f"Created subscription {stripe_subscription.id} for user {user.id}")
            
            return {
                "subscription_id": stripe_subscription.id,
                "status": stripe_subscription.status,
                "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret
                if stripe_subscription.latest_invoice.payment_intent else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise AppException(
                message="Failed to create subscription",
                status_code=500,
                error_code="STRIPE_ERROR",
                data={"error": str(e)}
            )
    
    async def update_subscription(
        self,
        user: User,
        new_plan: SubscriptionPlan,
        db: Session
    ) -> Dict[str, Any]:
        """Update existing subscription to new plan"""
        try:
            subscription = db.query(Subscription).filter_by(user_id=user.id).first()
            if not subscription or not subscription.stripe_subscription_id:
                raise AppException(
                    message="No active subscription found",
                    status_code=404,
                    error_code="NO_SUBSCRIPTION"
                )
            
            # Handle downgrade to free
            if new_plan == SubscriptionPlan.FREE:
                return await self.cancel_subscription(user, db)
            
            # Get Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )
            
            # Update subscription
            updated_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    "id": stripe_subscription["items"]["data"][0].id,
                    "price": self.PLANS[new_plan]["stripe_price_id"]
                }],
                proration_behavior="always_invoice"  # Immediately charge/credit
            )
            
            # Update database
            subscription.plan = new_plan
            subscription.stripe_price_id = self.PLANS[new_plan]["stripe_price_id"]
            subscription.features = self.PLANS[new_plan]["features"]
            subscription.usage_limits = self.PLANS[new_plan]["features"]
            subscription.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Updated subscription for user {user.id} to plan {new_plan}")
            
            return {
                "subscription_id": updated_subscription.id,
                "plan": new_plan.value,
                "status": updated_subscription.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {str(e)}")
            raise AppException(
                message="Failed to update subscription",
                status_code=500,
                error_code="STRIPE_ERROR"
            )
    
    async def cancel_subscription(
        self,
        user: User,
        db: Session,
        immediate: bool = False
    ) -> Dict[str, Any]:
        """Cancel subscription"""
        try:
            subscription = db.query(Subscription).filter_by(user_id=user.id).first()
            if not subscription or not subscription.stripe_subscription_id:
                raise AppException(
                    message="No active subscription found",
                    status_code=404,
                    error_code="NO_SUBSCRIPTION"
                )
            
            # Cancel in Stripe
            if immediate:
                # Cancel immediately
                cancelled_subscription = stripe.Subscription.delete(
                    subscription.stripe_subscription_id
                )
            else:
                # Cancel at period end
                cancelled_subscription = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Update database
            if immediate:
                subscription.status = "cancelled"
                subscription.plan = SubscriptionPlan.FREE
                subscription.features = self.PLANS[SubscriptionPlan.FREE]["features"]
                subscription.usage_limits = self.PLANS[SubscriptionPlan.FREE]["features"]
                subscription.cancelled_at = datetime.utcnow()
            else:
                subscription.cancel_at_period_end = True
                subscription.cancelled_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Cancelled subscription for user {user.id}")
            
            return {
                "status": "cancelled" if immediate else "scheduled_for_cancellation",
                "cancel_at": subscription.current_period_end.isoformat() if not immediate else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {str(e)}")
            raise AppException(
                message="Failed to cancel subscription",
                status_code=500,
                error_code="STRIPE_ERROR"
            )
    
    async def create_payment_intent(
        self,
        user: User,
        amount: int,
        currency: str = "usd",
        description: str = None,
        metadata: Dict[str, Any] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payment"""
        try:
            # Get or create customer
            customer_id = await self.create_customer(user, db)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                description=description,
                metadata={
                    "user_id": str(user.id),
                    **(metadata or {})
                },
                automatic_payment_methods={"enabled": True}
            )
            
            # Record payment in database
            if db:
                payment = Payment(
                    user_id=user.id,
                    amount=amount,
                    currency=currency.upper(),
                    description=description,
                    stripe_payment_intent_id=intent.id,
                    status=PaymentStatus.PENDING,
                    metadata=metadata or {}
                )
                db.add(payment)
                db.commit()
            
            logger.info(f"Created payment intent {intent.id} for user {user.id}")
            
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount,
                "currency": currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise AppException(
                message="Failed to create payment",
                status_code=500,
                error_code="STRIPE_ERROR"
            )
    
    async def handle_webhook(self, payload: str, sig_header: str, db: Session) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            logger.info(f"Received webhook event: {event['type']}")
            
            # Handle different event types
            if event["type"] == "payment_intent.succeeded":
                await self._handle_payment_success(event["data"]["object"], db)
                
            elif event["type"] == "payment_intent.payment_failed":
                await self._handle_payment_failure(event["data"]["object"], db)
                
            elif event["type"] == "customer.subscription.created":
                await self._handle_subscription_created(event["data"]["object"], db)
                
            elif event["type"] == "customer.subscription.updated":
                await self._handle_subscription_updated(event["data"]["object"], db)
                
            elif event["type"] == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event["data"]["object"], db)
                
            elif event["type"] == "invoice.payment_succeeded":
                await self._handle_invoice_payment(event["data"]["object"], db)
                
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
            
            return {"status": "success", "event_type": event["type"]}
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise AppException(
                message="Invalid webhook signature",
                status_code=400,
                error_code="INVALID_SIGNATURE"
            )
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            raise AppException(
                message="Webhook processing failed",
                status_code=500,
                error_code="WEBHOOK_ERROR"
            )
    
    async def _handle_payment_success(self, payment_intent: Dict, db: Session):
        """Handle successful payment"""
        payment = db.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent["id"]
        ).first()
        
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            if payment_intent.get("charges", {}).get("data"):
                payment.stripe_charge_id = payment_intent["charges"]["data"][0]["id"]
            db.commit()
            logger.info(f"Payment {payment.id} marked as completed")
    
    async def _handle_payment_failure(self, payment_intent: Dict, db: Session):
        """Handle failed payment"""
        payment = db.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent["id"]
        ).first()
        
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = payment_intent.get("last_payment_error", {}).get("message")
            db.commit()
            logger.info(f"Payment {payment.id} marked as failed")
    
    async def _handle_subscription_created(self, subscription: Dict, db: Session):
        """Handle subscription creation"""
        user_id = int(subscription["metadata"].get("user_id", 0))
        if not user_id:
            return
        
        sub = db.query(Subscription).filter_by(user_id=user_id).first()
        if sub:
            sub.stripe_subscription_id = subscription["id"]
            sub.status = subscription["status"]
            sub.current_period_start = datetime.fromtimestamp(
                subscription["current_period_start"]
            )
            sub.current_period_end = datetime.fromtimestamp(
                subscription["current_period_end"]
            )
            db.commit()
            logger.info(f"Subscription created for user {user_id}")
    
    async def _handle_subscription_updated(self, subscription: Dict, db: Session):
        """Handle subscription update"""
        sub = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription["id"]
        ).first()
        
        if sub:
            sub.status = subscription["status"]
            sub.current_period_start = datetime.fromtimestamp(
                subscription["current_period_start"]
            )
            sub.current_period_end = datetime.fromtimestamp(
                subscription["current_period_end"]
            )
            sub.cancel_at_period_end = subscription.get("cancel_at_period_end", False)
            db.commit()
            logger.info(f"Subscription {sub.id} updated")
    
    async def _handle_subscription_deleted(self, subscription: Dict, db: Session):
        """Handle subscription deletion"""
        sub = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription["id"]
        ).first()
        
        if sub:
            sub.status = "cancelled"
            sub.plan = SubscriptionPlan.FREE
            sub.features = self.PLANS[SubscriptionPlan.FREE]["features"]
            sub.usage_limits = self.PLANS[SubscriptionPlan.FREE]["features"]
            sub.cancelled_at = datetime.utcnow()
            db.commit()
            logger.info(f"Subscription {sub.id} cancelled")
    
    async def _handle_invoice_payment(self, invoice: Dict, db: Session):
        """Handle invoice payment"""
        # Record payment
        if invoice.get("subscription") and invoice.get("customer"):
            sub = db.query(Subscription).filter_by(
                stripe_subscription_id=invoice["subscription"]
            ).first()
            
            if sub:
                payment = Payment(
                    user_id=sub.user_id,
                    subscription_id=sub.id,
                    amount=invoice["amount_paid"],
                    currency=invoice["currency"].upper(),
                    description=f"Subscription payment for {sub.plan.value} plan",
                    stripe_invoice_id=invoice["id"],
                    stripe_charge_id=invoice.get("charge"),
                    status=PaymentStatus.COMPLETED,
                    completed_at=datetime.utcnow()
                )
                db.add(payment)
                db.commit()
                logger.info(f"Recorded invoice payment for subscription {sub.id}")
    
    async def get_payment_methods(self, user: User) -> List[Dict[str, Any]]:
        """Get user's payment methods"""
        try:
            subscription = await self._get_subscription(user.id)
            if not subscription or not subscription.stripe_customer_id:
                return []
            
            payment_methods = stripe.PaymentMethod.list(
                customer=subscription.stripe_customer_id,
                type="card"
            )
            
            return [
                {
                    "id": pm.id,
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year,
                    "is_default": pm.id == stripe.Customer.retrieve(
                        subscription.stripe_customer_id
                    ).invoice_settings.default_payment_method
                }
                for pm in payment_methods.data
            ]
            
        except stripe.error.StripeError as e:
            logger.error(f"Error fetching payment methods: {str(e)}")
            return []
    
    async def check_feature_access(
        self,
        user: User,
        feature_key: str,
        db: Session
    ) -> Dict[str, Any]:
        """Check if user has access to a feature"""
        subscription = db.query(Subscription).filter_by(user_id=user.id).first()
        
        if not subscription:
            # Create free subscription if doesn't exist
            subscription = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.FREE,
                status="active",
                features=self.PLANS[SubscriptionPlan.FREE]["features"],
                usage_limits=self.PLANS[SubscriptionPlan.FREE]["features"]
            )
            db.add(subscription)
            db.commit()
        
        features = subscription.features or self.PLANS[subscription.plan]["features"]
        limit = features.get(feature_key, 0)
        
        return {
            "has_access": limit != 0,
            "limit": limit if limit != -1 else None,  # -1 means unlimited
            "is_unlimited": limit == -1
        }
    
    async def track_usage(
        self,
        user: User,
        metric_name: str,
        quantity: float,
        db: Session
    ):
        """Track usage for metered features"""
        subscription = db.query(Subscription).filter_by(user_id=user.id).first()
        if not subscription:
            return
        
        # Get current period
        period_start = subscription.current_period_start or datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        period_end = subscription.current_period_end or (
            period_start + timedelta(days=30)
        )
        
        # Check existing usage record
        usage = db.query(UsageRecord).filter(
            and_(
                UsageRecord.subscription_id == subscription.id,
                UsageRecord.metric_name == metric_name,
                UsageRecord.period_start == period_start,
                UsageRecord.period_end == period_end
            )
        ).first()
        
        if usage:
            usage.quantity += quantity
            usage.recorded_at = datetime.utcnow()
        else:
            usage = UsageRecord(
                subscription_id=subscription.id,
                metric_name=metric_name,
                quantity=quantity,
                period_start=period_start,
                period_end=period_end
            )
            db.add(usage)
        
        db.commit()
    
    async def get_usage_summary(
        self,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Get usage summary for current period"""
        subscription = db.query(Subscription).filter_by(user_id=user.id).first()
        if not subscription:
            return {}
        
        # Get current period
        period_start = subscription.current_period_start or datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        period_end = subscription.current_period_end or (
            period_start + timedelta(days=30)
        )
        
        # Get usage records
        usage_records = db.query(UsageRecord).filter(
            and_(
                UsageRecord.subscription_id == subscription.id,
                UsageRecord.period_start == period_start,
                UsageRecord.period_end == period_end
            )
        ).all()
        
        # Build summary
        usage_summary = {}
        limits = subscription.usage_limits or self.PLANS[subscription.plan]["features"]
        
        for record in usage_records:
            usage_summary[record.metric_name] = {
                "used": record.quantity,
                "limit": limits.get(record.metric_name, 0),
                "percentage": (record.quantity / limits.get(record.metric_name, 1)) * 100
                if limits.get(record.metric_name, 0) > 0 else 0
            }
        
        # Add unused metrics
        for metric, limit in limits.items():
            if metric not in usage_summary and isinstance(limit, (int, float)):
                usage_summary[metric] = {
                    "used": 0,
                    "limit": limit if limit != -1 else None,
                    "percentage": 0
                }
        
        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "usage": usage_summary
        }
    
    async def _get_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's subscription (helper method)"""
        # This would typically use the session from the caller
        # For now, returning None to indicate it should be fetched in the calling method
        return None


# Global payment service instance
payment_service = PaymentService()