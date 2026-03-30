import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
import httpx

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

app = FastAPI(title="AI Real Estate Deals API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    import stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
    else:
        stripe = None
except Exception:
    stripe = None
    STRIPE_SECRET_KEY = ""
    STRIPE_PUBLISHABLE_KEY = ""

try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    groq_client = None
    GROQ_API_KEY = ""

SUBSCRIPTION_PLANS = {
    "free": {"credits": 3, "price": 0, "name": "Free Trial"},
    "starter": {"credits": 15, "price": 9, "name": "Starter - 15 Analyses"},
    "pro": {"credits": 50, "price": 29, "name": "Pro - 50 Analyses"},
    "enterprise": {"credits": 200, "price": 99, "name": "Enterprise - 200 Analyses"},
}

DEMO_PROPERTIES = [
    {"id": 1, "title": "Luxury 6BR Villa with Private Beach - Palm Jumeirah", "price": 18500000, "currency": "AED", "area": 750, "city": "Dubai", "country": "UAE", "bedrooms": 6, "bathrooms": 7, "property_type": "villa", "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800", "location": "Palm Jumeirah", "description": "Exclusive beachfront villa with private pool, home theater, and staff quarters."},
    {"id": 2, "title": "2BR Luxury Apartment - Burj Khalifa View", "price": 2350000, "currency": "AED", "area": 145, "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800", "location": "Downtown Dubai", "description": "Stunning apartment with direct Burj Khalifa views."},
    {"id": 3, "title": "4BR Townhouse - Green Community", "price": 2850000, "currency": "AED", "area": 320, "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4, "property_type": "townhouse", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "location": "Arabian Ranches 3", "description": "Modern townhouse in family-friendly community with parks and schools."},
    {"id": 4, "title": "1BR Sea View Apartment - Marina Towers", "price": 1450000, "currency": "AED", "area": 95, "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1, "property_type": "apartment", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "location": "Dubai Marina", "description": "Bright apartment with stunning sea and marina views."},
    {"id": 5, "title": "3BR Duplex Penthouse - Business Bay", "price": 4200000, "currency": "AED", "area": 350, "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 4, "property_type": "penthouse", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800", "location": "Business Bay", "description": "Luxury duplex penthouse with private terrace and canal views."},
]

class UserDB:
    def __init__(self):
        self.users = {}
        self.verification_codes = {}
        self.analyses = []
        self._init_demo()
    
    def _init_demo(self):
        demo_email = "test@demo.com"
        self.users[demo_email] = {
            "id": 1,
            "email": demo_email,
            "password_hash": self._hash_password("demo123"),
            "full_name": "Demo User",
            "credits": 100,
            "plan": "free",
            "email_verified": True,
            "created_at": datetime.utcnow().isoformat(),
            "stripe_customer_id": None,
            "subscription_id": None
        }
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, password: str, full_name: str = "") -> dict:
        if email in self.users:
            raise ValueError("Email already registered")
        
        user_id = len(self.users) + 1
        code = secrets.token_hex(16)
        
        self.users[email] = {
            "id": user_id,
            "email": email,
            "password_hash": self._hash_password(password),
            "full_name": full_name or email.split("@")[0],
            "credits": SUBSCRIPTION_PLANS["free"]["credits"],
            "plan": "free",
            "email_verified": False,
            "created_at": datetime.utcnow().isoformat(),
            "stripe_customer_id": None,
            "subscription_id": None
        }
        
        self.verification_codes[email] = code
        return {"email": email, "verification_code": code}
    
    def verify_user(self, email: str, code: str) -> bool:
        if self.verification_codes.get(email) == code:
            if email in self.users:
                self.users[email]["email_verified"] = True
                self.verification_codes.pop(email, None)
                return True
        return False
    
    def authenticate(self, email: str, password: str) -> Optional[dict]:
        user = self.users.get(email)
        if user and user["password_hash"] == self._hash_password(password):
            return user
        return None
    
    def get_user(self, email: str) -> Optional[dict]:
        return self.users.get(email)
    
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        for user in self.users.values():
            if user["id"] == user_id:
                return user
        return None
    
    def update_credits(self, email: str, credits: int, plan: str = None):
        if email in self.users:
            self.users[email]["credits"] += credits
            if plan:
                self.users[email]["plan"] = plan
    
    def use_credit(self, email: str) -> bool:
        if email in self.users and self.users[email]["credits"] > 0:
            self.users[email]["credits"] -= 1
            return True
        return False
    
    def add_analysis(self, email: str, analysis: dict):
        self.analyses.append({**analysis, "user_email": email, "created_at": datetime.utcnow().isoformat()})
    
    def get_user_analyses(self, email: str, limit: int = 20):
        user_analyses = [a for a in self.analyses if a.get("user_email") == email]
        return user_analyses[-limit:][::-1]

user_db = UserDB()

class TokenData(BaseModel):
    email: Optional[str] = None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = user_db.get_user(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_verified_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("email_verified"):
        raise HTTPException(status_code=403, detail="Email not verified")
    return current_user

async def get_ai_analysis_groq(property_data: dict, user_budget: dict) -> str:
    if not groq_client:
        return None
    
    prompt = f"""Analyze this property for real estate investment:
Property: {property_data['title']}
Price: {property_data['price']:,} {property_data['currency']}
Area: {property_data['area']} sqm
Location: {property_data['location']}, {property_data['city']}
Bedrooms: {property_data['bedrooms']}, Bathrooms: {property_data['bathrooms']}
User Budget: {user_budget.get('budget_min', 0):,} - {user_budget.get('budget_max', 99999999):,}

Provide a brief investment analysis (under 60 words):
1. Deal Score (0-100)
2. Price vs Market estimate
3. Key highlights
4. Investment recommendation (Buy/Hold/Avoid)"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception:
        return None

@app.get("/")
def root():
    return {"message": "AI Real Estate Deals API", "version": "2.0.0", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "groq_configured": bool(groq_client), "stripe_configured": bool(stripe)}

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/v1/auth/register")
def register(request: RegisterRequest):
    try:
        result = user_db.create_user(request.email, request.password, request.full_name)
        token = create_access_token({"sub": request.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"email": request.email, "credits": SUBSCRIPTION_PLANS["free"]["credits"]},
            "verification_code": result["verification_code"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/auth/login")
def login(request: LoginRequest):
    user = user_db.authenticate(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "credits": user["credits"],
            "plan": user["plan"],
            "email_verified": user["email_verified"]
        }
    }

@app.post("/api/v1/auth/verify-email")
def verify_email(email: str, code: str):
    if user_db.verify_user(email, code):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid verification code")

@app.get("/api/v1/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "credits": current_user["credits"],
        "plan": current_user["plan"],
        "email_verified": current_user["email_verified"],
        "created_at": current_user["created_at"]
    }

@app.get("/api/v1/auth/refresh")
def refresh_token(current_user: dict = Depends(get_current_user)):
    token = create_access_token({"sub": current_user["email"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/v1/properties")
def get_properties(
    city: str = None,
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
    if property_type:
        filtered = [p for p in filtered if property_type.lower() in p["property_type"].lower()]
    if min_price:
        filtered = [p for p in filtered if p["price"] >= min_price]
    if max_price:
        filtered = [p for p in filtered if p["price"] <= max_price]
    if bedrooms:
        filtered = [p for p in filtered if p.get("bedrooms", 0) >= bedrooms]
    
    start = (page - 1) * per_page
    return {
        "items": filtered[start:start + per_page],
        "total": len(filtered),
        "page": page,
        "per_page": per_page
    }

@app.get("/api/v1/properties/{property_id}")
def get_property(property_id: int):
    prop = next((p for p in DEMO_PROPERTIES if p["id"] == property_id), None)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return {**prop, "deal_score": 88.5, "price_vs_market": -7.2}

class AnalyzeRequest(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_city: Optional[str] = None
    bedrooms_min: Optional[int] = None

@app.post("/api/v1/analyze")
async def analyze_property(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_verified_user)
):
    if not user_db.use_credit(current_user["email"]):
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    suitable = [p for p in DEMO_PROPERTIES if p["price"] <= (request.budget_max or 5000000)]
    if request.budget_min:
        suitable = [p for p in suitable if p["price"] >= request.budget_min]
    if request.preferred_city:
        suitable = [p for p in suitable if request.preferred_city.lower() in p["city"].lower()]
    if request.bedrooms_min:
        suitable = [p for p in suitable if p.get("bedrooms", 0) >= request.bedrooms_min]
    
    analysis = {
        "id": len(user_db.analyses) + 1,
        "budget_min": request.budget_min,
        "budget_max": request.budget_max,
        "preferred_city": request.preferred_city,
        "matches": len(suitable),
        "properties": suitable[:5],
        "insights": f"Found {len(suitable)} properties. Avg price: {sum(p['price'] for p in suitable) / max(len(suitable), 1):,.0f} AED."
    }
    
    user_db.add_analysis(current_user["email"], analysis)
    return analysis

class SingleAnalyzeRequest(BaseModel):
    property_id: int

@app.post("/api/v1/analyze/single")
async def analyze_single_property(
    request: SingleAnalyzeRequest,
    current_user: dict = Depends(get_verified_user)
):
    if not user_db.use_credit(current_user["email"]):
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    prop = next((p for p in DEMO_PROPERTIES if p["id"] == request.property_id), None)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    ai_insight = None
    if groq_client:
        user_budget = {"budget_min": 0, "budget_max": 99999999}
        ai_insight = await get_ai_analysis_groq(prop, user_budget)
    
    analysis = {
        "id": len(user_db.analyses) + 1,
        "property": prop,
        "ai_insight": ai_insight,
        "ai_enabled": bool(groq_client)
    }
    
    user_db.add_analysis(current_user["email"], analysis)
    return analysis

@app.get("/api/v1/analyze/history")
def get_analysis_history(current_user: dict = Depends(get_verified_user)):
    return user_db.get_user_analyses(current_user["email"])

@app.get("/api/v1/plans")
def get_plans():
    return SUBSCRIPTION_PLANS

@app.get("/api/v1/plans/pricing")
def get_pricing():
    return {
        "plans": SUBSCRIPTION_PLANS,
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY
    }

@app.post("/api/v1/billing/create-checkout-session")
def create_checkout_session(plan_id: str, current_user: dict = Depends(get_verified_user)):
    if not stripe:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    if plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": plan["name"]},
                    "unit_amount": int(plan["price"] * 100)
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/pricing",
            metadata={"email": current_user["email"], "plan_id": plan_id}
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/v1/billing/webhook")
async def stripe_webhook(request: Request):
    if not stripe or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session["metadata"]["email"]
        plan_id = session["metadata"]["plan_id"]
        
        if email in user_db.users and plan_id in SUBSCRIPTION_PLANS:
            user_db.update_credits(email, SUBSCRIPTION_PLANS[plan_id]["credits"], plan_id)
    
    return {"received": True}

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
