from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    credits: int
    is_premium: bool
    referral_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PropertyBase(BaseModel):
    title: str
    price: float
    area: float
    city: str
    location: Optional[str] = None
    district: Optional[str] = None


class PropertyCreate(PropertyBase):
    description: Optional[str] = None
    country: str = "USA"
    currency: str = "USD"
    currency_symbol: str = "$"
    region: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None


class PropertyResponse(PropertyBase):
    id: int
    currency: str
    currency_symbol: str
    region: Optional[str]
    price_per_m2: Optional[float]
    country: str
    property_type: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyWithScore(PropertyResponse):
    deal_score: float
    price_vs_market: float
    recommendation: str


class AnalysisRequest(BaseModel):
    budget_min: Optional[float] = 0
    budget_max: Optional[float] = None
    preferred_city: Optional[str] = None
    preferred_country: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms_min: Optional[int] = None


class AnalysisResponse(BaseModel):
    id: int
    deal_score: float
    price_vs_market: float
    recommendation: str
    insights: dict
    top_properties: List[PropertyWithScore]
    created_at: datetime

    class Config:
        from_attributes = True


class CreditPackage(BaseModel):
    id: str
    credits: int
    price_cents: int
    price_display: str


class CheckoutSession(BaseModel):
    package_id: str
    success_url: str
    cancel_url: str


class TransactionResponse(BaseModel):
    id: int
    amount: int
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_analyses: int
    credits_remaining: int
    top_deal_score: Optional[float]
    recent_analyses: List[AnalysisResponse]


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., description="Property listing URL to analyze")


class MarketComparison(BaseModel):
    market_avg_price_per_m2: Optional[float] = None
    your_price_per_m2: Optional[float] = None
    difference_percent: Optional[float] = None
    note: Optional[str] = None


class URLAnalysisResponse(BaseModel):
    success: bool
    source: Optional[str] = None
    url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    currency_symbol: Optional[str] = None
    area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_m2: Optional[float] = None
    deal_score: Optional[float] = None
    market_comparison: Optional[MarketComparison] = None
    error: Optional[str] = None
