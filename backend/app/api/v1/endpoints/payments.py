"""
Payment and subscription API endpoints
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import stripe

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subscription import SubscriptionPlan, PaymentStatus
from app.services.payment_service import payment_service
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Request/Response Models
class CreateSubscriptionRequest(BaseModel):
    plan: SubscriptionPlan
    payment_method_id: str


class UpdateSubscriptionRequest(BaseModel):
    plan: SubscriptionPlan


class CreatePaymentRequest(BaseModel):
    amount: int  # in cents
    currency: str = "usd"
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AddPaymentMethodRequest(BaseModel):
    payment_method_id: str
    set_as_default: bool = True


@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    plans = []
    for plan_key, plan_data in payment_service.PLANS.items():
        plans.append({
            "id": plan_key.value,
            "name": plan_data["name"],
            "price": plan_data["price"],
            "price_display": f"${plan_data['price'] / 100:.2f}" if plan_data["price"] > 0 else "Free",
            "features": plan_data["features"],
            "recommended": plan_key == SubscriptionPlan.PREMIUM
        })
    
    return {
        "plans": plans,
        "currency": "USD"
    }


@router.get("/subscription")
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription details"""
    subscription = db.query(payment_service.Subscription).filter_by(
        user_id=current_user.id
    ).first()
    
    if not subscription:
        # Return free plan if no subscription
        return {
            "plan": SubscriptionPlan.FREE.value,
            "status": "active",
            "features": payment_service.PLANS[SubscriptionPlan.FREE]["features"],
            "current_period_end": None,
            "cancel_at_period_end": False
        }
    
    return {
        "plan": subscription.plan.value,
        "status": subscription.status,
        "features": subscription.features,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "trial_end": subscription.trial_end
    }


@router.post("/subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new subscription"""
    try:
        result = await payment_service.create_subscription(
            user=current_user,
            plan=request.plan,
            payment_method_id=request.payment_method_id,
            db=db
        )
        
        return {
            "success": True,
            "subscription_id": result["subscription_id"],
            "status": result["status"],
            "client_secret": result.get("client_secret")
        }
    except Exception as e:
        logger.error(f"Subscription creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update existing subscription plan"""
    try:
        result = await payment_service.update_subscription(
            user=current_user,
            new_plan=request.plan,
            db=db
        )
        
        return {
            "success": True,
            "subscription_id": result["subscription_id"],
            "plan": result["plan"],
            "status": result["status"]
        }
    except Exception as e:
        logger.error(f"Subscription update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/subscription")
async def cancel_subscription(
    immediate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel subscription"""
    try:
        result = await payment_service.cancel_subscription(
            user=current_user,
            db=db,
            immediate=immediate
        )
        
        return {
            "success": True,
            "status": result["status"],
            "cancel_at": result.get("cancel_at")
        }
    except Exception as e:
        logger.error(f"Subscription cancellation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intent")
async def create_payment_intent(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent for one-time payment"""
    try:
        result = await payment_service.create_payment_intent(
            user=current_user,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
            db=db
        )
        
        return {
            "success": True,
            "payment_intent_id": result["payment_intent_id"],
            "client_secret": result["client_secret"],
            "amount": result["amount"],
            "currency": result["currency"]
        }
    except Exception as e:
        logger.error(f"Payment intent creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_user)
):
    """Get user's saved payment methods"""
    try:
        methods = await payment_service.get_payment_methods(current_user)
        return {
            "payment_methods": methods
        }
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        return {"payment_methods": []}


@router.post("/payment-methods")
async def add_payment_method(
    request: AddPaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new payment method"""
    try:
        # Get or create customer
        customer_id = await payment_service.create_customer(current_user, db)
        
        # Attach payment method
        payment_method = stripe.PaymentMethod.attach(
            request.payment_method_id,
            customer=customer_id
        )
        
        # Set as default if requested
        if request.set_as_default:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": request.payment_method_id}
            )
        
        return {
            "success": True,
            "payment_method": {
                "id": payment_method.id,
                "brand": payment_method.card.brand,
                "last4": payment_method.card.last4,
                "exp_month": payment_method.card.exp_month,
                "exp_year": payment_method.card.exp_year
            }
        }
    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/payment-methods/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a payment method"""
    try:
        stripe.PaymentMethod.detach(payment_method_id)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error removing payment method: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-history")
async def get_payment_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    from app.models.subscription import Payment
    
    payments = db.query(Payment).filter_by(
        user_id=current_user.id
    ).order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    
    total = db.query(Payment).filter_by(user_id=current_user.id).count()
    
    return {
        "payments": [
            {
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "description": payment.description,
                "status": payment.status.value,
                "created_at": payment.created_at,
                "completed_at": payment.completed_at
            }
            for payment in payments
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/usage")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current billing period usage summary"""
    try:
        usage = await payment_service.get_usage_summary(current_user, db)
        return usage
    except Exception as e:
        logger.error(f"Error fetching usage: {str(e)}")
        return {
            "period_start": None,
            "period_end": None,
            "usage": {}
        }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        result = await payment_service.handle_webhook(
            payload.decode('utf-8'),
            stripe_signature,
            db
        )
        return result
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feature-access/{feature_key}")
async def check_feature_access(
    feature_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has access to a specific feature"""
    access = await payment_service.check_feature_access(
        user=current_user,
        feature_key=feature_key,
        db=db
    )
    return access


# Utility endpoint for development
@router.post("/create-portal-session")
async def create_customer_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe customer portal session for subscription management"""
    try:
        from app.models.subscription import Subscription
        
        subscription = db.query(Subscription).filter_by(
            user_id=current_user.id
        ).first()
        
        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=404,
                detail="No customer account found"
            )
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/account/subscription"
        )
        
        return {
            "url": session.url
        }
    except Exception as e:
        logger.error(f"Portal session error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))