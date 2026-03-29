"""
Real Estate API Router - Open-Source RentCast Alternative
Provides property data, valuations, comparables, and market data
"""

from fastapi import APIRouter, Query, Path, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field

from app.services.real_estate_api import PropertyService
from app.services.real_estate_api.data_sources import PropertyRecord
from app.services.real_estate_api.valuation_engine import ValuationEngine
from app.services.auth import get_current_user
from app.models.models import User


router = APIRouter(prefix="/realestate", tags=["Real Estate API"])

# Initialize services
property_service = PropertyService()
valuation_engine = ValuationEngine()


# Request/Response Models

class PropertyRequest(BaseModel):
    address: str
    city: str
    state: str
    zipCode: Optional[str] = None
    propertyId: Optional[int] = None


class ValuationRequest(BaseModel):
    address: str
    city: str
    state: str
    zipCode: Optional[str] = None
    propertyId: Optional[int] = None
    includeComparables: bool = True


class ComparablesRequest(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    zipCode: Optional[str] = None
    propertyId: Optional[int] = None
    radiusMiles: float = 1.0
    limit: int = 10
    soldWithinDays: int = 365


class MarketRentRequest(BaseModel):
    city: str
    state: str
    zipCode: Optional[str] = None
    propertyType: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    squareFeet: Optional[int] = None


class InvestmentRequest(BaseModel):
    address: str
    city: str
    state: str
    zipCode: Optional[str] = None
    purchasePrice: Optional[float] = None
    downPaymentPct: float = 20
    interestRate: float = 7.0
    loanTermYears: int = 30
    monthlyRent: Optional[float] = None


class SearchFilters(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    county: Optional[str] = None
    propertyType: Optional[str] = None
    minBeds: Optional[int] = None
    maxBeds: Optional[int] = None
    minBaths: Optional[float] = None
    maxBaths: Optional[float] = None
    minSqft: Optional[int] = None
    maxSqft: Optional[int] = None
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None
    minYear: Optional[int] = None
    maxYear: Optional[int] = None


# API Response Models

class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class PropertyResponse(APIResponse):
    data: Optional[dict] = None


class PropertyListResponse(APIResponse):
    data: List[dict] = []
    total: int = 0
    limit: int = 100
    offset: int = 0


# PROPERTY ENDPOINTS

@router.get("/property", response_model=PropertyResponse)
async def get_property(
    address: Optional[str] = Query(None, description="Street address"),
    city: Optional[str] = Query(None, description="City name"),
    state: Optional[str] = Query(None, description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
    propertyId: Optional[int] = Query(None, description="Internal property ID"),
):
    """
    Get property details by address or ID.
    
    Mimics: GET /v1/property
    """
    result = await property_service.get_property(
        address=address,
        city=city,
        state=state,
        zip_code=zipCode,
        property_id=propertyId,
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return PropertyResponse(data=result)


@router.get("/property/{propertyId}", response_model=PropertyResponse)
async def get_property_by_id(
    propertyId: int = Path(..., description="Property ID"),
):
    """
    Get property by internal ID.
    """
    result = await property_service.get_property(property_id=propertyId)
    
    if not result:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return PropertyResponse(data=result)


@router.post("/property", response_model=PropertyResponse)
async def create_or_update_property(
    request: PropertyRequest,
):
    """
    Create or update a property record.
    """
    # For now, just return the property if it exists
    result = await property_service.get_property(
        address=request.address,
        city=request.city,
        state=request.state,
        zip_code=request.zipCode,
        property_id=request.propertyId,
    )
    
    return PropertyResponse(data=result)


# VALUATION ENDPOINTS

@router.get("/property/valuation", response_model=PropertyResponse)
async def get_valuation(
    address: str = Query(..., description="Street address"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
    propertyId: Optional[int] = Query(None, description="Internal property ID"),
    includeComparables: bool = Query(True, description="Include comparable sales"),
):
    """
    Get automated valuation (AVM) for a property.
    
    Mimics: GET /v1/property/valuation
    """
    result = await property_service.get_valuation(
        address=address,
        city=city,
        state=state,
        zip_code=zipCode,
        property_id=propertyId,
        include_comparables=includeComparables,
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Could not generate valuation")
    
    return PropertyResponse(data=result)


@router.post("/property/valuation", response_model=PropertyResponse)
async def create_valuation(
    request: ValuationRequest,
):
    """
    Create a property valuation.
    """
    result = await property_service.get_valuation(
        address=request.address,
        city=request.city,
        state=request.state,
        zip_code=request.zipCode,
        property_id=request.propertyId,
        include_comparables=request.includeComparables,
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Could not generate valuation")
    
    return PropertyResponse(data=result)


# COMPARABLES ENDPOINTS

@router.get("/property/comps", response_model=PropertyListResponse)
async def get_comparables(
    address: Optional[str] = Query(None, description="Subject property address"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
    propertyId: Optional[int] = Query(None, description="Internal property ID"),
    radiusMiles: float = Query(1.0, description="Search radius in miles"),
    limit: int = Query(10, description="Maximum number of comparables"),
    soldWithinDays: int = Query(365, description="Only properties sold within this period"),
):
    """
    Find comparable properties for valuation.
    
    Mimics: GET /v1/property/comps
    """
    results = await property_service.get_comparables(
        address=address,
        city=city,
        state=state,
        zip_code=zipCode,
        property_id=propertyId,
        radius_miles=radiusMiles,
        limit=limit,
        sold_within_days=soldWithinDays,
    )
    
    return PropertyListResponse(
        data=results,
        total=len(results),
        limit=limit,
        offset=0,
    )


@router.post("/property/comps", response_model=PropertyListResponse)
async def find_comparables(
    request: ComparablesRequest,
):
    """
    Find comparable properties.
    """
    results = await property_service.get_comparables(
        address=request.address,
        city=request.city,
        state=request.state,
        zip_code=request.zipCode,
        property_id=request.propertyId,
        radius_miles=request.radiusMiles,
        limit=request.limit,
        sold_within_days=request.soldWithinDays,
    )
    
    return PropertyListResponse(
        data=results,
        total=len(results),
        limit=request.limit,
        offset=0,
    )


# MARKET DATA ENDPOINTS

@router.get("/market/rent", response_model=PropertyResponse)
async def get_market_rent(
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
    propertyType: Optional[str] = Query(None, description="Property type"),
    bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
    bathrooms: Optional[float] = Query(None, description="Number of bathrooms"),
    squareFeet: Optional[int] = Query(None, description="Square footage"),
):
    """
    Get market rent estimate for a property type.
    
    Mimics: GET /v1/market/rent
    """
    result = await property_service.get_market_rent(
        city=city,
        state=state,
        zip_code=zipCode,
        property_type=propertyType,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_feet=squareFeet,
    )
    
    return PropertyResponse(data=result)


@router.post("/market/rent", response_model=PropertyResponse)
async def estimate_rent(
    request: MarketRentRequest,
):
    """
    Estimate market rent for a property.
    """
    result = await property_service.get_market_rent(
        city=request.city,
        state=request.state,
        zip_code=request.zipCode,
        property_type=request.propertyType,
        bedrooms=request.bedrooms,
        bathrooms=request.bathrooms,
        square_feet=request.squareFeet,
    )
    
    return PropertyResponse(data=result)


@router.get("/market/{city}", response_model=PropertyResponse)
async def get_market_data(
    city: str = Path(..., description="City name"),
    state: str = Query(..., description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
    county: Optional[str] = Query(None, description="County name"),
    propertyType: Optional[str] = Query(None, description="Property type filter"),
):
    """
    Get comprehensive market data for a location.
    
    Mimics: GET /v1/market/{city}
    """
    result = await property_service.get_market_data(
        city=city,
        state=state,
        zip_code=zipCode,
        county=county,
        property_type=propertyType,
    )
    
    return PropertyResponse(data=result)


@router.get("/market/{city}/trends", response_model=PropertyResponse)
async def get_market_trends(
    city: str = Path(..., description="City name"),
    state: str = Query(..., description="State code"),
    metric: str = Query("price", description="Metric to track (price, rent, inventory, sales)"),
    periods: int = Query(12, description="Number of periods (months) to return"),
):
    """
    Get historical market trends.
    
    Mimics: GET /v1/market/{city}/trends
    """
    from app.services.real_estate_api.market_analyzer import MarketAnalyzer
    analyzer = MarketAnalyzer()
    
    result = await analyzer.get_market_trends(
        city=city,
        state=state,
        metric=metric,
        periods=periods,
    )
    
    return PropertyResponse(data=result)


# SCHOOL DATA ENDPOINTS

@router.get("/schools", response_model=PropertyResponse)
async def get_school_data(
    address: str = Query(..., description="Property address"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
):
    """
    Get school data for a property location.
    
    Mimics: GET /v1/schools
    """
    result = await property_service.get_school_data(
        address=address,
        city=city,
        state=state,
        zip_code=zipCode,
    )
    
    return PropertyResponse(data=result)


# SEARCH ENDPOINTS

@router.get("/properties", response_model=PropertyListResponse)
async def search_properties(
    city: Optional[str] = Query(None, description="City filter"),
    state: Optional[str] = Query(None, description="State filter"),
    zipCode: Optional[str] = Query(None, description="ZIP code filter"),
    county: Optional[str] = Query(None, description="County filter"),
    propertyType: Optional[str] = Query(None, description="Property type filter"),
    minBeds: Optional[int] = Query(None, description="Minimum bedrooms"),
    maxBeds: Optional[int] = Query(None, description="Maximum bedrooms"),
    minBaths: Optional[float] = Query(None, description="Minimum bathrooms"),
    maxBaths: Optional[float] = Query(None, description="Maximum bathrooms"),
    minSqft: Optional[int] = Query(None, description="Minimum square footage"),
    maxSqft: Optional[int] = Query(None, description="Maximum square footage"),
    minPrice: Optional[float] = Query(None, description="Minimum price"),
    maxPrice: Optional[float] = Query(None, description="Maximum price"),
    minYear: Optional[int] = Query(None, description="Minimum year built"),
    maxYear: Optional[int] = Query(None, description="Maximum year built"),
    limit: int = Query(100, description="Maximum results", le=500),
    offset: int = Query(0, description="Pagination offset"),
):
    """
    Search for properties matching criteria.
    
    Mimics: GET /v1/properties/search
    """
    results = await property_service.search_properties(
        city=city,
        state=state,
        zip_code=zipCode,
        county=county,
        property_type=propertyType,
        min_beds=minBeds,
        max_beds=maxBeds,
        min_baths=minBaths,
        max_baths=maxBaths,
        min_sqft=minSqft,
        max_sqft=maxSqft,
        min_price=minPrice,
        max_price=maxPrice,
        min_year=minYear,
        max_year=maxYear,
        limit=limit,
        offset=offset,
    )
    
    return PropertyListResponse(
        data=results,
        total=len(results),
        limit=limit,
        offset=offset,
    )


@router.post("/properties/search", response_model=PropertyListResponse)
async def search_properties_post(
    filters: SearchFilters,
    limit: int = Query(100, description="Maximum results", le=500),
    offset: int = Query(0, description="Pagination offset"),
):
    """
    Search for properties with filters.
    """
    results = await property_service.search_properties(
        city=filters.city,
        state=filters.state,
        zip_code=filters.zipCode,
        county=filters.county,
        property_type=filters.propertyType,
        min_beds=filters.minBeds,
        max_beds=filters.maxBeds,
        min_baths=filters.minBaths,
        max_baths=filters.maxBaths,
        min_sqft=filters.minSqft,
        max_sqft=filters.maxSqft,
        min_price=filters.minPrice,
        max_price=filters.maxPrice,
        min_year=filters.minYear,
        max_year=filters.maxYear,
        limit=limit,
        offset=offset,
    )
    
    return PropertyListResponse(
        data=results,
        total=len(results),
        limit=limit,
        offset=offset,
    )


# INVESTMENT ANALYSIS ENDPOINTS

@router.get("/investment", response_model=PropertyResponse)
async def calculate_investment(
    address: str = Query(..., description="Property address"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State code"),
    zipCode: Optional[str] = Query(None, description="ZIP code"),
    purchasePrice: Optional[float] = Query(None, description="Purchase price"),
    downPaymentPct: float = Query(20, description="Down payment percentage"),
    interestRate: float = Query(7.0, description="Annual interest rate"),
    loanTermYears: int = Query(30, description="Loan term in years"),
    monthlyRent: Optional[float] = Query(None, description="Expected monthly rent"),
):
    """
    Calculate investment metrics for a property.
    
    Mimics: GET /v1/property/investment
    """
    result = property_service.calculate_investment(
        address=address,
        city=city,
        state=state,
        zip_code=zipCode,
        purchase_price=purchasePrice,
        down_payment_pct=downPaymentPct,
        interest_rate=interestRate,
        loan_term_years=loanTermYears,
        monthly_rent=monthlyRent,
    )
    
    return PropertyResponse(data=result)


@router.post("/investment", response_model=PropertyResponse)
async def analyze_investment(
    request: InvestmentRequest,
):
    """
    Analyze investment potential of a property.
    """
    result = property_service.calculate_investment(
        address=request.address,
        city=request.city,
        state=request.state,
        zip_code=request.zipCode,
        purchase_price=request.purchasePrice,
        down_payment_pct=request.downPaymentPct,
        interest_rate=request.interestRate,
        loan_term_years=request.loanTermYears,
        monthly_rent=request.monthlyRent,
    )
    
    return PropertyResponse(data=result)


# BATCH ENDPOINTS

@router.post("/batch/property", response_model=PropertyResponse)
async def batch_get_properties(
    requests: List[PropertyRequest],
):
    """
    Get multiple properties in a single request.
    
    Mimics: POST /v1/property/batch
    """
    results = []
    for req in requests[:50]:  # Limit to 50 properties
        result = await property_service.get_property(
            address=req.address,
            city=req.city,
            state=req.state,
            zip_code=req.zipCode,
            property_id=req.propertyId,
        )
        if result:
            results.append(result)
    
    return PropertyResponse(
        data={"properties": results},
        total=len(results),
    )


@router.post("/batch/valuation", response_model=PropertyResponse)
async def batch_get_valuations(
    requests: List[ValuationRequest],
):
    """
    Get multiple property valuations in a single request.
    
    Mimics: POST /v1/property/valuation/batch
    """
    results = []
    for req in requests[:20]:  # Limit to 20 valuations
        result = await property_service.get_valuation(
            address=req.address,
            city=req.city,
            state=req.state,
            zip_code=req.zipCode,
            property_id=req.propertyId,
            include_comparables=req.includeComparables,
        )
        if result:
            results.append(result)
    
    return PropertyResponse(
        data={"valuations": results},
        total=len(results),
    )
