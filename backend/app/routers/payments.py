"""
Stripe Payment Router with Subscription Support
Free: 3 analyses/day | Pro: $9/month unlimited
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import User, Transaction
from app.schemas.schemas import TransactionResponse
from app.services.auth import get_current_user, add_credits
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])

PLANS = {
    "free": {
        "name": "Free",
        "price_cents": 0,
        "price_display": "$0",
        "analyses_per_day": 3,
        "stripe_price_id": None,
        "features": ["3 analyses/day", "Basic deal scoring", "50+ countries", "Email support"]
    },
    "pro_monthly": {
        "name": "Pro Monthly",
        "price_cents": 900,
        "price_display": "$9/month",
        "analyses_per_day": 999999,
        "stripe_price_id": settings.STRIPE_PRO_PRICE_ID or "price_pro_monthly",
        "features": ["Unlimited analyses", "Advanced scoring", "Market trends", "Priority support", "API access"]
    },
    "investor": {
        "name": "Investor",
        "price_cents": 2900,
        "price_display": "$29/month",
        "analyses_per_day": 999999,
        "stripe_price_id": settings.STRIPE_INVESTOR_PRICE_ID or "price_investor_monthly",
        "features": ["Everything in Pro", "API access", "Custom alerts", "Portfolio tracking", "Dedicated support"]
    }
}


def get_stripe():
    """Get Stripe client with error handling"""
    if not settings.STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe
    except ImportError:
        return None


class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price_cents: int
    price_display: str
    features: List[str]


class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    success_url: str
    cancel_url: str


class SubscriptionResponse(BaseModel):
    checkout_url: Optional[str] = None
    subscription_id: Optional[str] = None
    status: str
    plan: str
    message: Optional[str] = None


@router.get("/plans", response_model=List[SubscriptionPlan])
def get_subscription_plans():
    """Get available subscription plans"""
    return [
        SubscriptionPlan(
            id=plan_id,
            name=plan["name"],
            price_cents=plan["price_cents"],
            price_display=plan["price_display"],
            features=plan["features"]
        )
        for plan_id, plan in PLANS.items()
    ]


@router.get("/current")
def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current subscription status"""
    is_pro = current_user.is_premium
    plan = "investor" if is_pro and "investor" in str(current_user.subscription_status) else "pro_monthly" if is_pro else "free"
    
    return {
        "plan": plan,
        "plan_name": PLANS[plan]["name"],
        "is_premium": is_pro,
        "subscription_status": current_user.subscription_status,
        "credits": current_user.credits,
        "analyses_today": 0,
        "daily_limit": PLANS[plan]["analyses_per_day"]
    }


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe subscription for Pro/Investor plan"""
    stripe = get_stripe()
    
    if not stripe:
        return SubscriptionResponse(
            status="demo",
            plan="free",
            message="Stripe not configured. Running in demo mode."
        )
    
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = PLANS[request.plan_id]
    
    if plan["stripe_price_id"] is None or plan["price_cents"] == 0:
        raise HTTPException(status_code=400, detail="Free plan does not need subscription")
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"AI Deals Finder - {plan['name']}",
                            "description": f"Unlimited property analysis with {plan['name']} plan",
                        },
                        "unit_amount": plan["price_cents"],
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "plan_id": request.plan_id,
            },
            customer_email=current_user.email,
        )
        
        return SubscriptionResponse(
            checkout_url=checkout_session.url,
            status="pending",
            plan=request.plan_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    stripe = get_stripe()
    
    if not stripe:
        return {"status": "webhook_disabled"}
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        user_id = int(metadata.get("user_id", 0))
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            plan_id = metadata.get("plan_id", "pro_monthly")
            if session.get("subscription"):
                user.is_premium = True
                user.stripe_subscription_id = session.get("subscription")
                user.subscription_status = plan_id
                if session.get("customer"):
                    user.stripe_customer_id = session.get("customer")
            db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.is_premium = False
            user.subscription_status = "cancelled"
            db.commit()
    
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = "past_due"
            db.commit()
    
    return {"status": "success"}


@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel user's subscription"""
    stripe = get_stripe()
    
    if not stripe or not current_user.stripe_subscription_id:
        current_user.is_premium = False
        current_user.subscription_status = "cancelled"
        db.commit()
        return {"status": "cancelled", "message": "Subscription cancelled"}
    
    try:
        stripe.Subscription.cancel(current_user.stripe_subscription_id)
        current_user.is_premium = False
        current_user.subscription_status = "cancelled"
        db.commit()
        return {"status": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).all()
    return transactions
