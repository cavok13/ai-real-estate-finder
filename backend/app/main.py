from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, properties, analysis, payments, quick_analyze, realestate_api, markets

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered real estate deal finder that analyzes properties and scores investment opportunities"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3013",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3013",
    ],
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


@app.get("/health")
def health_check():
    return {"status": "healthy"}
