from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Real Estate Deals Finder"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database - Use SQLite for local dev
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./real_estate.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRO_PRICE_ID: Optional[str] = os.getenv("STRIPE_PRO_PRICE_ID")
    STRIPE_INVESTOR_PRICE_ID: Optional[str] = os.getenv("STRIPE_INVESTOR_PRICE_ID")
    
    # RentCast API (for real property data)
    RENTCAST_API_KEY: Optional[str] = os.getenv("RENTCAST_API_KEY")
    
    # Frontend URL (for Stripe redirects)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # AI Settings
    DEAL_THRESHOLD: float = 0.15  # 15% below average = good deal
    TOP_DEALS_COUNT: int = 5
    
    # Free plan limits
    FREE_ANALYSES_PER_DAY: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
