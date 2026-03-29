from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, properties, analysis, payments, quick_analyze, realestate_api, markets
from app.database import SessionLocal
from app.models.models import User
from app.services.auth import get_password_hash

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered real estate deal finder that analyzes properties and scores investment opportunities"
)

# CORS middleware - allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(properties.router, prefix=settings.API_V1_STR)
app.include_router(analysis.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(quick_analyze.router)  # No prefix, uses /api/v1/analyze
app.include_router(realestate_api.router, prefix=settings.API_V1_STR)  # Real Estate API (RentCast alternative)
app.include_router(markets.router, prefix=settings.API_V1_STR)  # UAE Markets + Unified Analyzer


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Real Estate Deals Finder API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/test-login")
def test_login():
    return {"access_token": "demo-token", "token_type": "bearer"}


@app.post("/api/v1/auth/demo-login")
def demo_login(request: dict):
    email = request.get("email", "")
    password = request.get("password", "")
    if email == "test@demo.com" and password == "demo123":
        return {"access_token": "demo-access-token", "token_type": "bearer"}
    return {"error": "Invalid credentials"}, 401


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
def create_demo_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "test@demo.com").first()
        if not existing:
            demo_user = User(
                email="test@demo.com",
                full_name="Demo User",
                hashed_password=get_password_hash("demo123"),
                is_active=True,
                referral_code="DEMO2024"
            )
            db.add(demo_user)
            db.commit()
            print("Demo user created: test@demo.com / demo123")
    finally:
        db.close()
