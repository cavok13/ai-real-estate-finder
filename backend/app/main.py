import os
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Optional

try:
    from huggingface_hub import InferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

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
USE_HF = bool(HF_TOKEN and HF_AVAILABLE)


async def get_ai_analysis(property_data: dict, user_budget: dict) -> dict:
    """Get AI-powered property analysis using Hugging Face Inference Providers"""
    if not USE_HF or not HF_TOKEN:
        return None
    
    prompt = f"""Analyze this property for real estate investment in UAE:
Property: {property_data['title']}
Price: {property_data['price']:,} {property_data['currency']}
Area: {property_data['area']} sqm
Location: {property_data['location']}, {property_data['city']}
Bedrooms: {property_data['bedrooms']}, Bathrooms: {property_data['bathrooms']}
User Budget: {user_budget.get('budget_min', 0):,} - {user_budget.get('budget_max', 99999999):,}

Provide a brief investment analysis with:
1. Deal Score (0-100)
2. Price vs Market estimate
3. Key highlights
4. Investment recommendation (Buy/Hold/Avoid)
Keep it under 80 words."""

    try:
        client = InferenceClient(
            provider="auto",
            api_key=HF_TOKEN
        )
        
        response = client.text_generation(
            prompt,
            model="google/flan-t5-base",
            max_new_tokens=150,
            temperature=0.7,
            return_full_text=False
        )
        
        if response:
            return {"ai_analysis": response, "powered_by": "huggingface"}
    except Exception as e:
        print(f"HF API error: {e}")
        import traceback
        traceback.print_exc()
    return None

app = FastAPI(title="AI Real Estate Deals Finder API")

SUBSCRIPTION_PLANS = {
    "free": {"credits": 3, "price": 0},
    "basic": {"credits": 20, "price": 9, "name": "Basic - 20 Analyses", "stripe_link": "https://buy.stripe.com/4gMfZh7vs2P38dV8r4gfu02"},
    "pro": {"credits": 100, "price": 29, "name": "Pro - 100 Analyses", "stripe_link": "https://buy.stripe.com/3cI3cv3fc9drbq78r4gfu01"},
    "enterprise": {"credits": 500, "price": 79, "name": "Enterprise - 500 Analyses", "stripe_link": "https://buy.stripe.com/aFa4gz7vs0GV2TBcHkgfu00"},
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
    {"id": 21, "title": "1BR Apartment - Bluewaters Island", "price": 1650000, "currency": "AED", "area": 85, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Bluewaters Island", "description": "Modern apartment near Ain Dubai. Walking distance to beach and restaurants."},
    {"id": 22, "title": "3BR Villa - Arabian Ranches 2", "price": 3200000, "currency": "AED", "area": 380, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Arabian Ranches 2", "description": "Family villa in established community with pool and park access."},
    {"id": 23, "title": "Studio - Al Barsha", "price": 580000, "currency": "AED", "area": 48, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Barsha", "description": "Affordable studio near Mall of the Emirates. Great location and transport links."},
    {"id": 24, "title": "2BR Apartment - Jumeirah Beach Residence", "price": 1850000, "currency": "AED", "area": 130, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "JBR", "description": "Beachfront apartment with stunning sea views. Direct access to JBR beach and The Walk."},
    {"id": 25, "title": "5BR Villa - Green Community", "price": 4500000, "currency": "AED", "area": 550, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Emirates Living", "description": "Premium villa in Emirates Living. Near Springs and Meadows. Community pool and parks."},
    {"id": 26, "title": "1BR - Culture Village", "price": 980000, "currency": "AED", "area": 75, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Culture Village", "description": "Elegant apartment in heritage-style community near Dubai Creek."},
    {"id": 27, "title": "3BR Townhouse - Akoya Oxygen", "price": 2650000, "currency": "AED", "area": 260, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Akoya Oxygen", "description": "Modern townhouse in golf community. Trump World Golf Club nearby."},
    {"id": 28, "title": "2BR - Dubai Silicon Oasis", "price": 850000, "currency": "AED", "area": 100, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Dubai Silicon Oasis", "description": "Tech hub apartment near university. Good for investors renting to students."},
    {"id": 29, "title": "4BR Villa - Al Warqa", "price": 2200000, "currency": "AED", "area": 400, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Al Warqa", "description": "Spacious villa in established residential area. Near schools and shopping."},
    {"id": 30, "title": "Studio - Deira City Centre", "price": 520000, "currency": "AED", "area": 42, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Deira", "description": "Central studio near metro and City Centre Deira. Excellent rental yields."},
    {"id": 31, "title": "2BR - Business Bay Canal", "price": 1750000, "currency": "AED", "area": 115, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Business Bay", "description": "Canal view apartment in commercial hub. Walking distance to Dubai Mall."},
    {"id": 32, "title": "3BR Penthouse - Marina", "price": 4500000, "currency": "AED", "area": 320, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "penthouse", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800", "location": "Dubai Marina", "description": "Luxury penthouse with marina views. Private terrace and premium amenities."},
    {"id": 33, "title": "1BR - Al Hamra Village", "price": 680000, "currency": "AED", "area": 70, "city": "Ras Al Khaimah", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Hamra", "description": "Beach community apartment in RAK. Golf course and marina access."},
    {"id": 34, "title": "5BR Villa - Damac Hills 2", "price": 3800000, "currency": "AED", "area": 420, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Damac Hills 2", "description": "Family villa in new golf community. Affordable with great amenities."},
    {"id": 35, "title": "2BR - Abu Dhabi City Centre", "price": 1050000, "currency": "AED", "area": 105, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Al Danah", "description": "Central apartment near malls and hospitals. Family-friendly area."},
    {"id": 36, "title": "Studio - Discovery Gardens", "price": 620000, "currency": "AED", "area": 52, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Discovery Gardens", "description": "Garden-view studio in established community. Near Ibn Battuta Mall."},
    {"id": 37, "title": "3BR Townhouse - Mudon", "price": 2400000, "currency": "AED", "area": 230, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Mudon", "description": "Modern townhouse in family community. Schools and retail nearby."},
    {"id": 38, "title": "2BR - Fujairah Beach", "price": 750000, "currency": "AED", "area": 90, "city": "Fujairah", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Fujairah Beach", "description": "Beachfront apartment in Fujairah. Mountain views and peaceful location."},
    {"id": 39, "title": "4BR Villa - The Springs", "price": 4800000, "currency": "AED", "area": 480, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "The Springs", "description": "Lakeside villa in premium Springs community. Near meadows and schools."},
    {"id": 40, "title": "1BR - Ajman Corniche", "price": 420000, "currency": "AED", "area": 65, "city": "Ajman", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Ajman Corniche", "description": "Sea view apartment in Ajman. Affordable with good rental returns."},
    {"id": 41, "title": "3BR Apartment - Dubai Creek Harbour", "price": 2200000, "currency": "AED", "area": 170, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Dubai Creek Harbour", "description": "Futuristic waterfront apartment with Creek and skyline views."},
    {"id": 42, "title": "2BR Townhouse - Town Square", "price": 1750000, "currency": "AED", "area": 150, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Town Square", "description": "Affordable townhouse in new community. Central location with parks."},
    {"id": 43, "title": "5BR Villa - Al Barari", "price": 6500000, "currency": "AED", "area": 600, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Al Barari", "description": "Lush green villa in botanical community. Private garden and nature views."},
    {"id": 44, "title": "Studio - Motor City", "price": 590000, "currency": "AED", "area": 47, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Motor City", "description": "Sports city studio near motor racing circuit. Family-friendly area."},
    {"id": 45, "title": "2BR - Khalifa City A", "price": 1200000, "currency": "AED", "area": 120, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Khalifa City", "description": "Spacious apartment near airport and Yas Island. Good family area."},
    {"id": 46, "title": "3BR Penthouse - Burj Khalifa", "price": 8500000, "currency": "AED", "area": 400, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 4, "property_type": "penthouse", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800", "location": "Downtown Dubai", "description": "Iconic penthouse on top floors of Burj Khalifa. Unmatched views."},
    {"id": 47, "title": "1BR - Media City", "price": 1100000, "currency": "AED", "area": 80, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Dubai Media City", "description": "Tech and media hub apartment. Near beach and Palm Jumeirah."},
    {"id": 48, "title": "4BR Villa - Al Waha", "price": 2600000, "currency": "AED", "area": 380, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Al Waha", "description": "Affordable villa in new community. Good value for families."},
    {"id": 49, "title": "2BR - Downtown Muroor", "price": 950000, "currency": "AED", "area": 95, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Muroor", "description": "Central Abu Dhabi apartment near embassy district. Good connectivity."},
    {"id": 50, "title": "Studio - Greens", "price": 650000, "currency": "AED", "area": 50, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "The Greens", "description": "Greens view studio near golf course. Quiet residential area."},
    {"id": 51, "title": "3BR Apartment - The Address Residences", "price": 3200000, "currency": "AED", "area": 200, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Downtown Dubai", "description": "Luxury apartment in iconic Address hotel. Fountain and mall views."},
    {"id": 52, "title": "2BR - Sharjah Rolla", "price": 550000, "currency": "AED", "area": 85, "city": "Sharjah", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Al Rolla", "description": "Central Sharjah apartment near university. Good for students."},
    {"id": 53, "title": "5BR Villa - Jumeirah Park", "price": 5800000, "currency": "AED", "area": 520, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Jumeirah Park", "description": "Family villa near Jumeirah. Private garden and community pool."},
    {"id": 54, "title": "1BR - Al Nahda", "price": 480000, "currency": "AED", "area": 70, "city": "Sharjah", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Nahda", "description": "Border area apartment near Dubai. Affordable with easy commute."},
    {"id": 55, "title": "3BR Townhouse -Mira", "price": 2000000, "currency": "AED", "area": 210, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Mira", "description": "Affordable townhouse in Reem community. Good for first-time buyers."},
    {"id": 56, "title": "2BR - Al Raha Gardens", "price": 1350000, "currency": "AED", "area": 130, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Al Raha Gardens", "description": "Garden apartment in gated community. Near airport and city."},
    {"id": 57, "title": "4BR Villa - Villanova", "price": 2900000, "currency": "AED", "area": 360, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Villanova", "description": "Modern villa in new community. Payment plans available."},
    {"id": 58, "title": "Studio - IMPZ", "price": 450000, "currency": "AED", "area": 42, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "IMPZ", "description": "Media production zone studio. Good for creative professionals."},
    {"id": 59, "title": "3BR - Saadiyat Beach", "price": 2800000, "currency": "AED", "area": 190, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Saadiyat Beach", "description": "Cultural island beach apartment. Near museums and universities."},
    {"id": 60, "title": "2BR Townhouse - Dubai South", "price": 1500000, "currency": "AED", "area": 140, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Dubai South", "description": "Near Expo airport. Affordable with future growth potential."},
    {"id": 61, "title": "5BR Villa - Jumeirah Islands", "price": 7500000, "currency": "AED", "area": 650, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Jumeirah Islands", "description": "Waterfront villa in exclusive islands. Private and luxurious."},
    {"id": 62, "title": "1BR - Dubai Investment Park", "price": 680000, "currency": "AED", "area": 72, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "DIP", "description": "Industrial area apartment near schools. Good rental area."},
    {"id": 63, "title": "3BR Apartment - Emaar Beachfront", "price": 3500000, "currency": "AED", "area": 180, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Emaar Beachfront", "description": "Beachfront apartment with Dubai Marina views. Private beach access."},
    {"id": 64, "title": "2BR - Al Marjan Island", "price": 850000, "currency": "AED", "area": 95, "city": "Ras Al Khaimah", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Al Marjan Island", "description": "Island resort apartment. Beach and casino nearby."},
    {"id": 65, "title": "4BR Villa - Damac Lakes", "price": 4200000, "currency": "AED", "area": 450, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Damac Lakes", "description": "Golf villa with lake views. Premium community amenities."},
    {"id": 66, "title": "Studio - Arabian Center", "price": 520000, "currency": "AED", "area": 45, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Khawaneej", "description": "Affordable studio near Arabian Center Mall."},
    {"id": 67, "title": "3BR - Masdar City", "price": 1650000, "currency": "AED", "area": 160, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Masdar City", "description": "Eco-city sustainable apartment. Near university and airport."},
    {"id": 68, "title": "2BR Townhouse - Sobha Hartland", "price": 1950000, "currency": "AED", "area": 155, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Sobha Hartland", "description": "Quality townhouse near Dubai Hills. International schools nearby."},
    {"id": 69, "title": "5BR Villa - Althani", "price": 9000000, "currency": "AED", "area": 700, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 7, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Al Thanyah", "description": "Golf villa with plot. Premium finishes and location."},
    {"id": 70, "title": "1BR - Liwan", "price": 450000, "currency": "AED", "area": 65, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Liwan", "description": "Affordable Dubai South apartment. Future Expo area."},
    {"id": 71, "title": "3BR - Reem Hills", "price": 2400000, "currency": "AED", "area": 185, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Reem Hills", "description": "New island community apartment. Beach and nature."},
    {"id": 72, "title": "2BR - Aljada", "price": 1150000, "currency": "AED", "area": 110, "city": "Sharjah", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Aljada", "description": "New Sharjah master community. Great investment."},
    {"id": 73, "title": "4BR Villa - Fairway Vistas", "price": 5100000, "currency": "AED", "area": 480, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Dubai Hills Estate", "description": "Golf course villa near mall. Premium community."},
    {"id": 74, "title": "Studio - Remraam", "price": 550000, "currency": "AED", "area": 48, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Remraam", "description": "Affordable community studio near International City."},
    {"id": 75, "title": "3BR - Al Jurf", "price": 1800000, "currency": "AED", "area": 170, "city": "Ajman", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Al Jurf", "description": "New Ajman community apartment. Sea view options."},
    {"id": 76, "title": "2BR Townhouse - Nad Al Hamar", "price": 1650000, "currency": "AED", "area": 145, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Nad Al Hamar", "description": "Central townhouse near Rashidiya. Established area."},
    {"id": 77, "title": "5BR Villa - Mohammed Bin Rashid", "price": 12000000, "currency": "AED", "area": 800, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 7, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "MBR City", "description": "Mega villa in MBR City. District One views. Payment plans."},
    {"id": 78, "title": "1BR - The Onyx", "price": 1250000, "currency": "AED", "area": 78, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Business Bay", "description": "Business Bay tower near Downtown. Canal views."},
    {"id": 79, "title": "3BR - Bloomfields", "price": 2100000, "currency": "AED", "area": 175, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Meydan", "description": "Modern apartment near Meydan Racecourse. Good value."},
    {"id": 80, "title": "2BR - Al Tayy", "price": 1350000, "currency": "AED", "area": 125, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Al Tai", "description": "New Abu Dhabi community. Near highway and island."},
    {"id": 81, "title": "4BR Villa - Al Waha", "price": 3100000, "currency": "AED", "area": 390, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Al Waha", "description": "Gated villa community. Parks and pools."},
    {"id": 82, "title": "Studio - Barsha Heights", "price": 620000, "currency": "AED", "area": 52, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Barsha Heights", "description": "Tech view studio near metro. Great for professionals."},
    {"id": 83, "title": "3BR - Yas Acres", "price": 3200000, "currency": "AED", "area": 250, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Yas Acres", "description": "Golf villa on Yas Island. Near Ferrari World."},
    {"id": 84, "title": "2BR - Al Zahra", "price": 980000, "currency": "AED", "area": 100, "city": "Sharjah", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Al Zahra", "description": "Central Sharjah apartment near university."},
    {"id": 85, "title": "5BR Villa - District One", "price": 8500000, "currency": "AED", "area": 650, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "MBR City", "description": "Crystal lagoon villa. Private beach access."},
    {"id": 86, "title": "1BR - Al Quoz", "price": 850000, "currency": "AED", "area": 70, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Quoz", "description": "Artistic area apartment near galleries and cafes."},
    {"id": 87, "title": "3BR - Mina Road", "price": 1950000, "currency": "AED", "area": 165, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Mina Road", "description": "Sea view apartment near Mina Port. Good location."},
    {"id": 88, "title": "2BR Townhouse - Cerise", "price": 1800000, "currency": "AED", "area": 148, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Polan", "description": "Quality townhouse near Damac Hills. Good value."},
    {"id": 89, "title": "4BR Villa - Seashore", "price": 5500000, "currency": "AED", "area": 520, "city": "Ras Al Khaimah", "country": "UAE", "bedrooms": 4, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Seih Al Udebbi", "description": "Beachfront villa in RAK. Mountain backdrop."},
    {"id": 90, "title": "Studio - Karama", "price": 480000, "currency": "AED", "area": 40, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Karama", "description": "Central Karama studio nearBur Dubai. Excellent location."},
    {"id": 91, "title": "3BR - Maryah Island", "price": 2600000, "currency": "AED", "area": 180, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Maryah Island", "description": "Financial hub apartment near Cleveland Clinic."},
    {"id": 92, "title": "2BR - Al Mizhar", "price": 1050000, "currency": "AED", "area": 105, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Al Mizhar", "description": "Near airport. Affordable and convenient."},
    {"id": 93, "title": "5BR Villa - Haya", "price": 4800000, "currency": "AED", "area": 470, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 6, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Al Yelay 1", "description": "New villa community. Payment plan available."},
    {"id": 94, "title": "1BR - Al Karama", "price": 720000, "currency": "AED", "area": 75, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Karama", "description": "Central Karama apartment near metro. Shoppping and dining."},
    {"id": 95, "title": "3BR - Al Hili", "price": 1500000, "currency": "AED", "area": 155, "city": "Al Ain", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Al Hili", "description": "Al Ain apartment near university and parks."},
    {"id": 96, "title": "2BR Townhouse - Al Rashidiya", "price": 1700000, "currency": "AED", "area": 145, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Al Rashidiya", "description": "Near airport and metro. Good family area."},
    {"id": 97, "title": "4BR Villa - Marjan", "price": 4200000, "currency": "AED", "area": 420, "city": "Ras Al Khaimah", "country": "UAE", "bedrooms": 4, "bathrooms": 5, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Marjan Island", "description": "Island villa in RAK. Beach and casino nearby."},
    {"id": 98, "title": "Studio - Al Nahda 2", "price": 490000, "currency": "AED", "area": 44, "city": "Sharjah", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "studio", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Nahda 2", "description": "Border area studio near Dubai. Good commute."},
    {"id": 99, "title": "3BR - Al Sawan", "price": 1850000, "currency": "AED", "area": 160, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Al Sawan", "description": "Near beach and Mina Seyahi. Established area."},
    {"id": 100, "title": "2BR - Ajman Promenade", "price": 680000, "currency": "AED", "area": 90, "city": "Ajman", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "location": "Ajman Promenade", "description": "New Ajman apartment near Sheikh Mohammed Bin Zayed Road."},
    {"id": 101, "title": "5BR Villa - Al Marasy", "price": 6800000, "currency": "AED", "area": 580, "city": "Dubai", "country": "UAE", "bedrooms": 5, "bathrooms": 7, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Al Marasy", "description": "Waterfront villa near Business Bay. Premium finishes."},
    {"id": 102, "title": "1BR - Al Muteena", "price": 680000, "currency": "AED", "area": 65, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "location": "Al Muteena", "description": "Deira area apartment near Day to Day. Good rental."},
    {"id": 103, "title": "3BR - Al Raha Creek", "price": 2200000, "currency": "AED", "area": 175, "city": "Abu Dhabi", "country": "UAE", "bedrooms": 3, "bathrooms": 3, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Al Raha Creek", "description": "Creek view apartment in Al Raha. Near airport."},
    {"id": 104, "title": "2BR Townhouse - Liwan 2", "price": 1450000, "currency": "AED", "area": 135, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800", "location": "Liwan 2", "description": "New townhouse in Dubailand. Good value."},
    {"id": 105, "title": "4BR Villa - Al Awir", "price": 2800000, "currency": "AED", "area": 380, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800", "location": "Al Awir", "description": "Agricultural area villa. Near International City."},
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
async def analyze_property(
    budget_min: float = None,
    budget_max: float = None,
    preferred_city: str = None,
    bedrooms_min: int = None,
    property_id: int = None
):
    analysis_id = len(DEMO_ANALYSES) + 1
    
    suitable = [p for p in DEMO_PROPERTIES if p["price"] <= (budget_max or 5000000)]
    if budget_min:
        suitable = [p for p in suitable if p["price"] >= budget_min]
    if preferred_city:
        suitable = [p for p in suitable if preferred_city.lower() in p["city"].lower()]
    if bedrooms_min:
        suitable = [p for p in suitable if p.get("bedrooms", 0) >= bedrooms_min]
    
    ai_insight = None
    if property_id:
        prop = next((p for p in DEMO_PROPERTIES if p["id"] == property_id), None)
        if prop and USE_HF:
            user_budget = {"budget_min": budget_min or 0, "budget_max": budget_max or 99999999}
            ai_result = await get_ai_analysis(prop, user_budget)
            if ai_result:
                ai_insight = ai_result.get("ai_analysis")
    
    analysis = {
        "id": analysis_id,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferred_city": preferred_city,
        "bedrooms_min": bedrooms_min,
        "matches": len(suitable),
        "properties": suitable[:5],
        "insights": f"Found {len(suitable)} properties matching your criteria. Average price: {sum(p['price'] for p in suitable) / max(len(suitable), 1):,.0f} AED.",
        "ai_insight": ai_insight,
        "ai_enabled": USE_HF,
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
    return {
        "result": "API is working",
        "hf_enabled": USE_HF,
        "hf_token_prefix": HF_TOKEN[:10] + "..." if HF_TOKEN else None
    }


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
    """Create Stripe checkout session using payment links"""
    plan_id = request.get("plan_id", "pro")
    
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        return {"error": "Invalid plan"}, 400
    
    if plan["price"] == 0:
        return {"error": "Free plan doesn't need payment"}, 400
    
    stripe_link = plan.get("stripe_link")
    if stripe_link:
        return {"checkout_url": stripe_link, "session_id": plan_id, "is_payment_link": True}
    
    return {"error": "Payment link not available"}, 400


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
