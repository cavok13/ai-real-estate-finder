import os
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

try:
    import stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
    else:
        stripe = None
except Exception as e:
    print(f"Stripe import error: {e}")
    stripe = None
    STRIPE_SECRET_KEY = ""
    STRIPE_PUBLISHABLE_KEY = ""

HF_TOKEN = os.getenv("HF_TOKEN", "")
USE_HF = bool(HF_TOKEN)


async def get_ai_analysis(property_data: dict, user_budget: dict) -> dict:
    """Get AI-powered property analysis using Hugging Face"""
    if not USE_HF:
        return None
    
    prompt = f"""Analyze this property for real estate investment:
Property: {property_data['title']}
Price: {property_data['price']:,} {property_data['currency']}
Area: {property_data['area']} sqm
Location: {property_data['location']}, {property_data['city']}
Bedrooms: {property_data['bedrooms']}, Bathrooms: {property_data['bathrooms']}
User Budget: {user_budget.get('budget_min', 0):,} - {user_budget.get('budget_max', 99999999):,}

Provide a brief investment analysis with:
1. Deal Score (0-100)
2. Price vs Market (percentage)
3. Key highlights
4. Investment recommendation (Buy/Hold/Avoid)
Keep it under 100 words."""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-inference.huggingface.co/models/google/flan-t5-base",
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": prompt},
                timeout=30.0
            )
            if response.status_code == 200:
                result = response.json()
                return {"ai_analysis": result, "powered_by": "huggingface"}
    except Exception as e:
        print(f"HF API error: {e}")
    return None

app = FastAPI(title="AI Real Estate Deals Finder API")

SUBSCRIPTION_PLANS = {
    "free": {"credits": 3, "price": 0},
    "basic": {"credits": 20, "price": 19, "name": "Basic - 20 Analyses"},
    "pro": {"credits": 100, "price": 49, "name": "Pro - 100 Analyses"},
    "enterprise": {"credits": 500, "price": 149, "name": "Enterprise - 500 Analyses"},
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_USERS = {
    "test@demo.com": {"password": "demo123", "id": 1, "email": "test@demo.com", "full_name": "Demo User", "credits": 100, "plan": "free"}
}

DEMO_PROPERTIES = [
    {"id": 1, "title": "Luxury 6BR Villa with Private Beach - Palm Jumeirah", "price": 18500000, "currency": "AED", "area": 750, "city": "Dubai", "country": "UAE", "bedrooms": 6, "bathrooms": 7, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800", "location": "Palm Jumeirah", "description": "Exclusive beachfront villa with private pool, home theater, and staff quarters. Premium finishing with panoramic sea views."},
    {"id": 2, "title": "2BR Luxury Apartment - Burj Khalifa View", "price": 2350000, "currency": "AED", "area": 145, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Downtown Dubai", "description": "Stunning apartment with direct Burj Khalifa views. Fully furnished with premium amenities in Souk Al Bahar."},
    {"id": 3, "title": "4BR Townhouse - Green Community", "price": 2850000, "currency": "AED", "area": 320, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Arabian Ranches 3", "description": "Modern townhouse in family-friendly community with parks, schools, and retail outlets. Payment plan available."},
    {"id": 4, "title": "1BR Sea View Apartment - Marina Towers", "price": 1450000, "currency": "AED", "area": 95, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Dubai Marina", "description": "Bright apartment with stunning sea and marina views. Walking distance to JBR beach and metro."},
    {"id": 5, "title": "3BR Duplex Penthouse - Business Bay", "price": 4200000, "currency": "AED", "area": 350, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 4, "property_type": "penthouse", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800", "location": "Business Bay", "description": "Luxury duplex penthouse with private terrace and canal views. High-end finishes throughout."},
    {"id": 6, "title": "Studio Apartment - JLT Lakeside", "price": 720000, "currency": "AED", "area": 50, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "JLT", "description": "Modern studio in vibrant JLT community. Close to metro, restaurants, and lakes. Great investment opportunity."},
    {"id": 7, "title": "7BR Mansion - Emirates Hills", "price": 28000000, "currency": "AED", "area": 1200, "city": "Dubai", "country": "UAE", "bedrooms": 7, "bathrooms": 8, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Emirates Hills", "description": "Prestigious mansion on 15,000 sqft plot. Custom built with luxury finishes, gym, cinema, and infinity pool."},
    {"id": 8, "title": "2BR Premium Apartment - DIFC", "price": 2650000, "currency": "AED", "area": 155, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "DIFC", "description": "Premium apartment in financial district with high ceilings and city views. Building has concierge and pool."},
    {"id": 9, "title": "3BR Townhouse - Meydan Racecourse", "price": 2100000, "currency": "AED", "area": 220, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Meydan", "description": "Contemporary townhouse near Meydan Racecourse. Close to schools and retail. Payment plan available."},
    {"id": 10, "title": "2BR Sea View - Abu Dhabi Corniche", "price": 1150000, "currency": "AED", "area": 120, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800", "location": "Corniche", "description": "Beautiful apartment with stunning sea views on Abu Dhabi's famous Corniche. Walking distance to shopping malls."},
    {"id": 11, "title": "4BR Villa with Pool - Al Reef", "price": 2400000, "currency": "AED", "area": 400, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 4, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Al Reef", "description": "Stunning villa in gated community with private pool. Close to Yas Island and airports."},
    {"id": 12, "title": "1BR Apartment - Sharjah Waterfront", "price": 450000, "currency": "AED", "area": 75, "city": "Sharjah", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Majaz", "description": "Affordable apartment in Sharjah waterfront development. Great for investors. High rental yield potential."},
    {"id": 13, "title": "5BR Family Villa - Damac Hills", "price": 5500000, "currency": "AED", "area": 500, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Damac Hills", "description": "Spacious villa in premium golf community. Private garden, shared pool, and kids' play areas."},
    {"id": 14, "title": "Studio Investment Unit - JVC", "price": 550000, "currency": "AED", "area": 45, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "JVC", "description": "High-yield investment studio in JVC. Multiple payment plans available. Strong rental demand in area."},
    {"id": 15, "title": "2BR Apartment - Yas Island", "price": 1350000, "currency": "AED", "area": 110, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Yas Island", "description": "Modern apartment near theme parks and Ferrari World. High rental demand for tourists."},
    {"id": 16, "title": "3BR Penthouse - Palm Views", "price": 3800000, "currency": "AED", "area": 280, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "penthouse", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800", "location": "Palm Jumeirah", "description": "Penthouse with partial sea views and access to beach. Modern finishes with private balcony."},
    {"id": 17, "title": "Luxury 2BR - Dubai Hills Estate", "price": 1950000, "currency": "AED", "area": 135, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Dubai Hills Estate", "description": "Apartment in prestigious golf community near Dubai Hills Mall. Family-friendly with parks and schools."},
    {"id": 18, "title": "Townhouse - Tilal Al Ghaf", "price": 2550000, "currency": "AED", "area": 240, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Tilal Al Ghaf", "description": "Eco-friendly townhouse with private garden near lagoon. Modern sustainable community."},
    {"id": 19, "title": "1BR Affordable - International City", "price": 320000, "currency": "AED", "area": 55, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "International City", "description": "Budget-friendly apartment in diverse International City. Great rental yields. Close to Dragon Mart."},
    {"id": 20, "title": "4BR Villa - Rashed City", "price": 1800000, "currency": "AED", "area": 350, "city": "Sharjah", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Al Rashed City", "description": "Spacious villa in Sharjah at competitive price. Large plot, perfect for families."},
]

DEMO_ANALYSES = []

@app.get("/")
def root():
    return {"message": "Welcome to AI Real Estate Deals Finder API", "version": "3.0.0", "docs": "/docs"}


@app.post("/api/v1/auth/login")
def login(request: dict):
    email = request.get("email", "")
    password = request.get("password", "")
    
    if email in DEMO_USERS and DEMO_USERS[email]["password"] == password:
        return {"access_token": f"demo-token-{email}", "token_type": "bearer"}
    return {"error": "Invalid credentials"}, 401


@app.post("/api/v1/auth/register")
def register(request: dict):
    email = request.get("email", "")
    password = request.get("password", "")
    full_name = request.get("full_name", "")
    
    if email in DEMO_USERS:
        return {"error": "Email already registered"}, 400
    
    user_id = len(DEMO_USERS) + 1
    DEMO_USERS[email] = {
        "password": password,
        "id": user_id,
        "email": email,
        "full_name": full_name or email.split("@")[0],
        "credits": 3,
        "plan": "free"
    }
    return {"access_token": f"demo-token-{email}", "token_type": "bearer"}


@app.get("/api/v1/auth/me")
def get_me():
    return {"id": 1, "email": "test@demo.com", "full_name": "Demo User", "credits": 100, "plan": "free"}


@app.get("/api/v1/properties")
def get_properties(
    city: str = None,
    country: str = None,
    property_type: str = None,
    min_price: float = None,
    max_price: float = None,
    bedrooms: int = None,
    page: int = 1,
    per_page: int = 20
):
    filtered = DEMO_PROPERTIES.copy()
    
    if city:
        filtered = [p for p in filtered if city.lower() in p["city"].lower()]
    if country:
        filtered = [p for p in filtered if country.lower() in p["country"].lower()]
    if property_type:
        filtered = [p for p in filtered if property_type.lower() in p["property_type"].lower()]
    if min_price:
        filtered = [p for p in filtered if p["price"] >= min_price]
    if max_price:
        filtered = [p for p in filtered if p["price"] <= max_price]
    if bedrooms:
        filtered = [p for p in filtered if p.get("bedrooms", 0) >= bedrooms]
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "items": filtered[start:end],
        "total": len(filtered),
        "page": page,
        "per_page": per_page
    }


@app.get("/api/v1/properties/best-deals")
def get_best_deals(city: str = None, limit: int = 10):
    deals = sorted(DEMO_PROPERTIES, key=lambda x: x["price"] / max(x["area"], 1))[:limit]
    for deal in deals:
        deal["deal_score"] = round(85 + (deal["price"] / 100000), 1)
        deal["price_vs_market"] = round(-5 - (deal["price"] / 500000), 1)
        deal["recommendation"] = "Great deal! Below market average."
    return deals


@app.get("/api/v1/properties/{property_id}")
def get_property(property_id: int):
    prop = next((p for p in DEMO_PROPERTIES if p["id"] == property_id), None)
    if not prop:
        return {"error": "Property not found"}, 404
    prop = prop.copy()
    prop["deal_score"] = 88.5
    prop["price_vs_market"] = -7.2
    prop["recommendation"] = "Strong buy - excellent location and price."
    return prop


@app.get("/api/v1/analyze")
def analyze_property(
    budget_min: float = None,
    budget_max: float = None,
    preferred_city: str = None,
    bedrooms_min: int = None
):
    analysis_id = len(DEMO_ANALYSES) + 1
    
    suitable = [p for p in DEMO_PROPERTIES if p["price"] <= (budget_max or 5000000)]
    if budget_min:
        suitable = [p for p in suitable if p["price"] >= budget_min]
    if preferred_city:
        suitable = [p for p in suitable if preferred_city.lower() in p["city"].lower()]
    if bedrooms_min:
        suitable = [p for p in suitable if p.get("bedrooms", 0) >= bedrooms_min]
    
    analysis = {
        "id": analysis_id,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferred_city": preferred_city,
        "bedrooms_min": bedrooms_min,
        "matches": len(suitable),
        "properties": suitable[:5],
        "insights": f"Found {len(suitable)} properties matching your criteria. Average price: {sum(p['price'] for p in suitable) / max(len(suitable), 1):,.0f} AED.",
        "created_at": "2026-03-30T12:00:00Z"
    }
    DEMO_ANALYSES.append(analysis)
    return analysis


@app.get("/api/v1/analyze/history")
def get_analysis_history():
    return DEMO_ANALYSES[-10:][::-1]


@app.get("/api/v1/markets/uae/summary")
def get_market_summary():
    return {
        "market": "dubai",
        "avg_price_per_sqm": 1450,
        "price_change_12m": 8.5,
        "rental_yield": 5.2,
        "total_listings": 45000,
        "top_areas": [
            {"name": "Dubai Marina", "avg_price": 1650000, "yield": 5.5},
            {"name": "Downtown Dubai", "avg_price": 2100000, "yield": 4.8},
            {"name": "Palm Jumeirah", "avg_price": 4500000, "yield": 4.2},
            {"name": "JLT", "avg_price": 950000, "yield": 6.1},
            {"name": "Business Bay", "avg_price": 1200000, "yield": 5.8}
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/test")
def test():
    return {"result": "API is working"}


@app.get("/api/v1/payments/plans")
def get_plans():
    """Get available subscription plans"""
    plans = []
    for key, plan in SUBSCRIPTION_PLANS.items():
        plans.append({
            "id": key,
            "name": plan.get("name", key.title()),
            "credits": plan["credits"],
            "price": plan["price"],
            "is_popular": key == "pro"
        })
    return plans


@app.post("/api/v1/payments/create-checkout")
def create_checkout(request: dict):
    """Create Stripe checkout session"""
    plan_id = request.get("plan_id", "pro")
    success_url = request.get("success_url", "https://frontend-psi-two-35.vercel.app/dashboard?payment=success")
    cancel_url = request.get("cancel_url", "https://frontend-psi-two-35.vercel.app/dashboard?payment=cancelled")
    
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        return {"error": "Invalid plan"}, 400
    
    if plan["price"] == 0:
        return {"error": "Free plan doesn't need payment"}, 400
    
    if stripe is None or not STRIPE_SECRET_KEY:
        return {"checkout_url": f"/dashboard?payment=demo&plan={plan_id}", "demo": True, "message": "Stripe not configured - demo mode"}
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": plan.get("name", f"AI Real Estate - {plan_id.title()}"),
                        "description": f"{plan['credits']} property analyses",
                    },
                    "unit_amount": plan["price"] * 100,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        return {"checkout_url": f"/dashboard?payment=demo&plan={plan_id}", "demo": True, "message": "Stripe not configured - demo mode"}


@app.get("/api/v1/payments/verify/{session_id}")
def verify_payment(session_id: str):
    """Verify if payment was successful"""
    if stripe is None or not STRIPE_SECRET_KEY:
        return {"status": "demo", "message": "Demo mode"}
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            return {"status": "paid", "plan": "pro"}
        return {"status": "pending"}
    except:
        return {"status": "demo", "message": "Demo mode"}


@app.get("/api/v1/payments/config")
def get_payment_config():
    """Get Stripe public configuration"""
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "is_live": STRIPE_SECRET_KEY.startswith("sk_live") if STRIPE_SECRET_KEY else False,
    }
