import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="AI Real Estate Deals Finder API")

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
    {"id": 1, "title": "Luxury Villa in Palm Jumeirah", "price": 8500000, "currency": "AED", "area": 450, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800", "location": "Palm Jumeirah", "description": "Stunning beachfront villa with private pool"},
    {"id": 2, "title": "Modern Apartment in Downtown Dubai", "price": 1850000, "currency": "AED", "area": 120, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Downtown Dubai", "description": "Luxury apartment with view of Burj Khalifa"},
    {"id": 3, "title": "3BR Townhouse in Arabian Ranches", "price": 2200000, "currency": "AED", "area": 250, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Arabian Ranches", "description": "Family townhouse in gated community"},
    {"id": 4, "title": "Sea View Apartment in Marina", "price": 1650000, "currency": "AED", "area": 110, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Dubai Marina", "description": "Stunning sea views, walk to beach"},
    {"id": 5, "title": "Penthouse in Business Bay", "price": 3200000, "currency": "AED", "area": 280, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 4, "property_type": "penthouse", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800", "location": "Business Bay", "description": "Luxury penthouse with panoramic views"},
    {"id": 6, "title": "Studio in JLT", "price": 650000, "currency": "AED", "area": 55, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "JLT", "description": "Modern studio in prime location"},
    {"id": 7, "title": "Villa in Emirates Hills", "price": 12000000, "currency": "AED", "area": 650, "city": "Dubai", "country": "UAE", "bedrooms": 6, "bathrooms": 7, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Emirates Hills", "description": "Exclusive villa in prime estate"},
    {"id": 8, "title": "2BR Apartment in DIFC", "price": 2100000, "currency": "AED", "area": 140, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "DIFC", "description": "Premium apartment in financial district"},
    {"id": 9, "title": "Townhouse in Meydan", "price": 1950000, "currency": "AED", "area": 200, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Meydan", "description": "Modern townhouse near racecourse"},
    {"id": 10, "title": "Apartment in Abu Dhabi Corniche", "price": 950000, "currency": "AED", "area": 100, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800", "location": "Corniche", "description": "Sea view apartment in prime location"},
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
