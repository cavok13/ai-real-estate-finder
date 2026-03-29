"""
Quick Analysis Router
Fast API endpoint for property analysis without authentication
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.property_analyzer import analyzer

router = APIRouter(prefix="/api/v1/analyze", tags=["Analysis"])


class QuickAnalyzeRequest(BaseModel):
    price: float = Field(..., gt=0, description="Property price")
    area: float = Field(..., gt=0, description="Property area in sqm")
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field("USA", description="Country name")
    rent_per_month: Optional[float] = Field(None, description="Expected monthly rent")


class MarketComparison(BaseModel):
    market_avg: float
    difference_percent: float
    comparison: str


class QuickAnalyzeResponse(BaseModel):
    pricePerSqm: float
    marketAvg: float
    roi: float
    score: int
    label: str
    market_comparison: MarketComparison
    insights: dict


@router.post("/quick", response_model=QuickAnalyzeResponse)
async def quick_analyze(request: QuickAnalyzeRequest):
    """
    Quick property analysis endpoint.
    Returns deal score, ROI estimate, and market comparison.
    
    No authentication required for quick analysis.
    """
    result = analyzer.analyze(
        price=request.price,
        area=request.area,
        city=request.city or "Unknown",
        country=request.country or "USA",
        rent_per_month=request.rent_per_month
    )
    
    price_diff_pct = ((result.marketAvg - result.pricePerSqm) / result.marketAvg) * 100
    
    if price_diff_pct > 10:
        comparison = "Significantly below market"
    elif price_diff_pct > 0:
        comparison = "Below market average"
    elif price_diff_pct > -10:
        comparison = "Near market value"
    else:
        comparison = "Above market value"
    
    insights = {
        "summary": f"This property is priced {abs(price_diff_pct):.1f}% {comparison.lower()}.",
        "recommendation": result.label,
        "estimated_yield": f"{result.roi:.1f}% annual return",
        "price_tier": "Budget" if result.pricePerSqm < 3000 else "Mid-range" if result.pricePerSqm < 8000 else "Premium"
    }
    
    return QuickAnalyzeResponse(
        pricePerSqm=result.pricePerSqm,
        marketAvg=result.marketAvg,
        roi=result.roi,
        score=result.score,
        label=result.label,
        market_comparison=MarketComparison(
            market_avg=result.marketAvg,
            difference_percent=round(price_diff_pct, 1),
            comparison=comparison
        ),
        insights=insights
    )


@router.get("/market/{city}")
async def get_market_data(city: str, country: str = "USA"):
    """
    Get market data for a specific city.
    Useful for comparing properties manually.
    """
    data = analyzer.get_market_data(city, country)
    return {
        "city": city,
        "country": country,
        "avg_price_sqm": data["avg_price_sqm"],
        "avg_rent_sqm": data["avg_rent_sqm"],
        "annual_growth": data["growth"]
    }
