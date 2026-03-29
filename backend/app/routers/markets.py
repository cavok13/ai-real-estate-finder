"""
Unified API Router - Combines all features
- UAE Market Data
- Global Property Analysis
- Credits System
- ROI & Deal Scoring
"""

import os
from fastapi import APIRouter, Query, Path, HTTPException, BackgroundTasks, Depends
from typing import Optional, List
from pydantic import BaseModel

from app.services.real_estate_api.uae_market import UAEMarketService
from app.services.property_analyzer_v2 import analyzer
from app.services.credits import (
    get_credits, get_user_plan, create_user, add_credits,
    consume_credit, require_credits, stripe_credits, PLAN_CREDITS, PLAN_PRICES
)


router = APIRouter(prefix="/markets", tags=["Markets & Analysis"])

uae_service = UAEMarketService()


# Request/Response Models

class AnalyzeURLRequest(BaseModel):
    url: str


class CreditPurchaseRequest(BaseModel):
    credit_pack: str  # 10_credits, 50_credits, 100_credits


# ─────────────────────────────────────────────────────────────
# UAE MARKET ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/uae/areas")
async def get_uae_areas(
    market: str = Query("dubai", description="Market: dubai or abu_dhabi"),
    sort_by: str = Query("yield", description="Sort by: yield, price, transactions"),
):
    """
    Get all UAE areas with market data.
    Built from Dubai Land Department 2024 data.
    """
    areas = uae_service.get_all_areas(market)
    
    if sort_by == "yield":
        areas.sort(key=lambda x: x["avgRentYield"], reverse=True)
    elif sort_by == "price":
        areas.sort(key=lambda x: x["avgPricePerSqFt"])
    elif sort_by == "transactions":
        areas.sort(key=lambda x: x["transactions2024"], reverse=True)
    
    return {
        "success": True,
        "market": market,
        "total_areas": len(areas),
        "areas": areas,
    }


@router.get("/uae/areas/{area_name}")
async def get_area_details(area_name: str):
    """Get detailed data for a specific area."""
    data = uae_service.get_area_data(area_name)
    
    if not data:
        raise HTTPException(status_code=404, detail="Area not found")
    
    return {"success": True, "area": data}


@router.get("/uae/best-roi")
async def get_best_roi_areas(
    market: str = Query("dubai", description="Market: dubai or abu_dhabi"),
    limit: int = Query(5, ge=1, le=20),
):
    """Get areas with best rental yield."""
    areas = uae_service.get_best_roi_areas(market, limit)
    return {"success": True, "market": market, "areas": areas}


@router.get("/uae/best-deals")
async def get_best_deals(
    market: str = Query("dubai", description="Market: dubai or abu_dhabi"),
):
    """Get areas with best deal potential (rising prices + high ROI)."""
    areas = uae_service.get_best_deal_areas(market)
    return {"success": True, "market": market, "areas": areas}


@router.get("/uae/summary")
async def get_market_summary(market: str = Query("dubai")):
    """Get overall market summary."""
    summary = uae_service.get_market_summary(market)
    return {"success": True, **summary}


# ─────────────────────────────────────────────────────────────
# PROPERTY ANALYSIS ENDPOINT
# ─────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_property_url(
    request: AnalyzeURLRequest,
    user_id: str = Depends(require_credits),
):
    """
    Analyze property from URL.
    Supports: Bayut, PropertyFinder, Zillow, Redfin, Realtor
    
    Returns:
    - roi_percent: Rental yield percentage
    - deal_score: 0-100 score
    - risk_level: Low/Medium/High
    - price_vs_market: Comparison to area average
    - tags: Array of tags like ["High ROI", "Undervalued"]
    - recommendation: Investment recommendation
    - data_source: Source of market data used
    """
    consume_credit(user_id)
    
    result = await analyzer.analyze_url(request.url)
    
    return {
        "success": result.get("success", True),
        "credits_remaining": get_credits(user_id),
        **result,
    }


@router.post("/analyze-free")
async def analyze_property_url_free(request: AnalyzeURLRequest):
    """
    Analyze property without API key (limited).
    Returns basic analysis only.
    """
    result = await analyzer.analyze_url(request.url)
    
    return {
        "success": result.get("success", True),
        "limited": True,
        "upgrade_url": "/api/v1/credits/buy",
        **result,
    }


@router.post("/analyze/batch")
async def analyze_properties_batch(
    requests: List[AnalyzeURLRequest],
    user_id: str = Depends(require_credits),
):
    """
    Analyze multiple properties at once.
    Consumes 1 credit per property.
    """
    results = []
    remaining_credits = get_credits(user_id)
    
    for req in requests[:min(len(requests), remaining_credits)]:
        try:
            result = await analyzer.analyze_url(req.url)
            results.append(result)
        except Exception as e:
            results.append({"success": False, "url": req.url, "error": str(e)})
    
    return {
        "success": True,
        "analyzed": len(results),
        "credits_remaining": get_credits(user_id) - len(results),
        "results": results,
    }


# ─────────────────────────────────────────────────────────────
# CREDITS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/credits/balance")
async def get_credits_balance(user_id: str = Depends(require_credits)):
    """Get current credits balance."""
    return {
        "success": True,
        "credits": get_credits(user_id),
        "plan": get_user_plan(user_id),
        "plan_credits": PLAN_CREDITS.get(get_user_plan(user_id), 10),
    }


@router.get("/credits/packs")
async def get_credit_packs():
    """Get available credit packs for purchase."""
    return {
        "success": True,
        "packs": stripe_credits.get_credit_packs(),
    }


@router.post("/credits/buy")
async def buy_credits(
    request: CreditPurchaseRequest,
    user_id: str = Depends(require_credits),
):
    """
    Buy credits via Stripe payment link or checkout session.
    Returns a redirect URL for payment.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    result = await stripe_credits.create_checkout_session(
        user_id=user_id,
        credit_pack=request.credit_pack,
        success_url=f"{frontend_url}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_url}/credits/cancel",
    )
    
    # Include credit amount in response for user reference
    credits_amount = stripe_credits.get_credits_for_pack(request.credit_pack)
    
    return {
        "success": True,
        "credits": credits_amount,
        "payment_type": result.get("type", "checkout"),
        **result,
    }


@router.post("/credits/webhook")
async def credits_webhook(
    payload: bytes,
    stripe_signature: str = Query(...),
):
    """Stripe webhook endpoint for processing credit purchases."""
    result = stripe_credits.process_webhook(payload, stripe_signature)
    return result


# ─────────────────────────────────────────────────────────────
# API KEY ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post("/api-key/create")
async def create_api_key(plan: str = Query("free")):
    """Create new API key for external access."""
    import uuid
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    api_key = create_user(user_id, plan)
    
    return {
        "success": True,
        "user_id": user_id,
        "api_key": api_key,
        "plan": plan,
        "credits": get_credits(user_id),
        "usage": f"Add header: X-Api-Key: {api_key}",
    }


@router.get("/plans")
async def get_plans():
    """Get subscription plans."""
    return {
        "success": True,
        "plans": [
            {"id": "free", "name": "Free", "price": 0, "currency": "EUR", "credits": 10, "features": ["Basic analysis", "Limited markets"]},
            {"id": "starter", "name": "Starter", "price": 9, "currency": "EUR", "credits": 100, "features": ["Full analysis", "UAE + USA markets", "API access"]},
            {"id": "pro", "name": "Pro", "price": 29, "currency": "EUR", "credits": 500, "features": ["Priority analysis", "All markets", "Batch processing", "Webhooks"]},
            {"id": "investor", "name": "Investor", "price": 79, "currency": "EUR", "credits": 2000, "features": ["Unlimited analysis", "Custom integrations", "Dedicated support"]},
        ],
    }


# ─────────────────────────────────────────────────────────────
# GLOBAL MARKET ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/global/property-types")
async def get_global_property_types():
    """Get supported property types across all markets."""
    return {
        "success": True,
        "property_types": [
            {"id": "villa", "name": "Villa", "uae": "فيلا", "common_in": ["UAE", "USA", "UK"]},
            {"id": "townhouse", "name": "Townhouse", "uae": "تاون هاوس", "common_in": ["UAE", "USA", "UK"]},
            {"id": "apartment", "name": "Apartment", "uae": "شقة", "common_in": ["UAE", "USA", "UK", "Europe"]},
            {"id": "penthouse", "name": "Penthouse", "uae": "بنتهاوس", "common_in": ["UAE", "USA"]},
            {"id": "studio", "name": "Studio", "uae": "ستوديو", "common_in": ["UAE", "USA", "Europe"]},
            {"id": "office", "name": "Office", "uae": "مكتب", "common_in": ["UAE", "USA", "UK"]},
            {"id": "retail", "name": "Retail", "uae": "تجزئة", "common_in": ["UAE", "USA", "UK"]},
        ],
    }


@router.get("/health")
async def markets_health():
    """Health check for markets API."""
    return {
        "status": "healthy",
        "uae_areas": len(uae_service.areas),
        "dubai_areas": 24,
        "abu_dhabi_areas": 18,
        "data_source": "Dubai Land Department 2024",
    }
