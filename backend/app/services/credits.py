"""
Credit System for AI Deals Finder
Integrates with Stripe for buying credits and managing API usage.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException, Header, Depends

# In-memory store (replace with PostgreSQL/Redis for production)
_USER_CREDITS: Dict[str, int] = {}
_API_KEYS: Dict[str, str] = {}  # api_key → user_id
_USER_PLANS: Dict[str, str] = {}  # user_id → plan

PLAN_CREDITS = {
    "free": 10,
    "starter": 100,
    "pro": 500,
    "investor": 2000,
}

PLAN_PRICES = {
    "free": 0,
    "starter": 9,    # EUR
    "pro": 29,       # EUR
    "investor": 79,   # EUR
}


def create_user(user_id: str, plan: str = "free") -> str:
    """Create user with plan credits and generate API key."""
    api_key = f"adf_{uuid.uuid4().hex}"
    _API_KEYS[api_key] = user_id
    _USER_CREDITS[user_id] = PLAN_CREDITS.get(plan, 10)
    _USER_PLANS[user_id] = plan
    return api_key


def get_user_from_key(api_key: str) -> Optional[str]:
    return _API_KEYS.get(api_key)


def get_credits(user_id: str) -> int:
    return _USER_CREDITS.get(user_id, 0)


def get_user_plan(user_id: str) -> str:
    return _USER_PLANS.get(user_id, "free")


def add_credits(user_id: str, amount: int) -> int:
    _USER_CREDITS[user_id] = _USER_CREDITS.get(user_id, 0) + amount
    return _USER_CREDITS[user_id]


def set_user_plan(user_id: str, plan: str) -> None:
    _USER_PLANS[user_id] = plan
    if plan in PLAN_CREDITS:
        _USER_CREDITS[user_id] = PLAN_CREDITS[plan]


def consume_credit(user_id: str) -> None:
    """Deduct 1 credit. Raises 402 if none left."""
    current = _USER_CREDITS.get(user_id, 0)
    if current <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "no_credits",
                "message": "You have no credits left. Buy more at /credits/buy.",
                "buy_url": "/api/v1/credits/buy",
            },
        )
    _USER_CREDITS[user_id] = current - 1


async def require_credits(x_api_key: Optional[str] = Header(None)) -> str:
    """FastAPI dependency to require valid API key with credits."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "missing_api_key", "message": "API key required"},
        )
    
    user_id = get_user_from_key(x_api_key)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_api_key", "message": "Invalid API key"},
        )
    
    # Check credits before allowing request
    if get_credits(user_id) <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "no_credits",
                "message": "You have no credits left. Buy more credits.",
                "buy_url": "/api/v1/credits/buy",
            },
        )
    
    return user_id


async def optional_credits(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """FastAPI dependency - optional API key."""
    if not x_api_key:
        return None
    
    user_id = get_user_from_key(x_api_key)
    return user_id


class StripeCredits:
    """Stripe integration for buying credits."""
    
    def __init__(self):
        self.stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        
        # Stripe Price IDs (from Stripe Dashboard)
        self.credit_prices = {
            "10_credits": os.getenv("STRIPE_PRICE_10_CREDITS", ""),
            "50_credits": os.getenv("STRIPE_PRICE_50_CREDITS", ""),
            "100_credits": os.getenv("STRIPE_PRICE_100_CREDITS", ""),
        }
        
        # Stripe Payment Links (direct checkout URLs)
        self.payment_links = {
            "10_credits": "https://buy.stripe.com/4gMfZh7vs2P38dV8r4gfu02",
            "50_credits": "https://buy.stripe.com/3cI3cv3fc9drbq78r4gfu01",
            "100_credits": "https://buy.stripe.com/aFa4gz7vs0GV2TBcHkgfu00",
        }
        
        # Credit amounts per pack
        self.credit_amounts = {
            "10_credits": 10,
            "50_credits": 50,
            "100_credits": 100,
        }
    
    def get_price_id(self, credit_pack: str) -> Optional[str]:
        return self.credit_prices.get(credit_pack)
    
    def get_payment_link(self, credit_pack: str) -> Optional[str]:
        return self.payment_links.get(credit_pack)
    
    def get_credits_for_pack(self, credit_pack: str) -> int:
        return self.credit_amounts.get(credit_pack, 0)
    
    async def create_checkout_session(
        self, user_id: str, credit_pack: str, success_url: str, cancel_url: str
    ) -> Dict:
        """Create Stripe checkout session for credit purchase."""
        if not self.stripe_key:
            # Fallback: Return payment link
            payment_link = self.get_payment_link(credit_pack)
            if payment_link:
                return {
                    "redirect_url": payment_link,
                    "type": "payment_link",
                }
            raise HTTPException(
                status_code=500,
                detail={"error": "stripe_not_configured", "message": "Stripe not configured"},
            )
        
        price_id = self.get_price_id(credit_pack)
        if not price_id:
            # Try payment link
            payment_link = self.get_payment_link(credit_pack)
            if payment_link:
                return {
                    "redirect_url": payment_link,
                    "type": "payment_link",
                }
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_pack", "message": "Invalid credit pack"},
            )
        
        try:
            import stripe
            stripe.api_key = self.stripe_key
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id, "credit_pack": credit_pack},
            )
            
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "type": "checkout_session",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error": "stripe_error", "message": str(e)},
            )
    
    def get_credit_packs(self) -> list:
        """Get available credit packs with payment links."""
        return [
            {
                "id": "10_credits",
                "credits": 10,
                "name": "10 Credits",
                "price": "€2.99",
                "currency": "EUR",
                "payment_link": self.payment_links.get("10_credits"),
                "stripe_price_id": self.credit_prices.get("10_credits"),
            },
            {
                "id": "50_credits",
                "credits": 50,
                "name": "50 Credits",
                "price": "€9",
                "currency": "EUR",
                "payment_link": self.payment_links.get("50_credits"),
                "stripe_price_id": self.credit_prices.get("50_credits"),
                "popular": True,
            },
            {
                "id": "100_credits",
                "credits": 100,
                "name": "100 Credits",
                "price": "€17",
                "currency": "EUR",
                "payment_link": self.payment_links.get("100_credits"),
                "stripe_price_id": self.credit_prices.get("100_credits"),
            },
        ]
    
    def process_webhook(self, payload: bytes, signature: str) -> Dict:
        """Process Stripe webhook for credit purchase."""
        if not self.stripe_key:
            return {"status": "error", "message": "Stripe not configured"}
        
        if not self.stripe_webhook_secret:
            return {"status": "error", "message": "Webhook secret not configured"}
        
        try:
            import stripe
            stripe.api_key = self.stripe_key
            
            event = stripe.Webhook.construct_event(payload, signature, self.stripe_webhook_secret)
            
            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                user_id = session.get("metadata", {}).get("user_id")
                credit_pack = session.get("metadata", {}).get("credit_pack")
                
                if user_id and credit_pack:
                    credits = self.get_credits_for_pack(credit_pack)
                    add_credits(user_id, credits)
                    return {"status": "success", "user_id": user_id, "credits_added": credits}
            
            # Handle direct payment link purchases
            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                # Get credits from payment amount as fallback
                amount = session.get("amount_total", 0) / 100
                if amount >= 17.99:
                    credits = 100
                elif amount >= 9.99:
                    credits = 50
                elif amount >= 2.99:
                    credits = 10
                else:
                    credits = 0
                
                if credits > 0:
                    # Use client_reference_id or create a lookup
                    client_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
                    if client_id:
                        add_credits(client_id, credits)
                        return {"status": "success", "credits_added": credits}
            
            return {"status": "ignored"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


stripe_credits = StripeCredits()
