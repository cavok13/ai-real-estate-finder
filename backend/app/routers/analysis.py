from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import User, Analysis, Property
from app.schemas.schemas import AnalysisRequest, AnalysisResponse, PropertyWithScore, DashboardStats, URLAnalysisRequest, URLAnalysisResponse, MarketComparison
from app.services.auth import get_current_user, use_credit
from app.services.deal_scorer import DealScoringService
from app.services.property_analyzer import PropertyAnalyzer
import json

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/url", response_model=URLAnalysisResponse)
async def analyze_property_url(
    request: URLAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a property from its listing URL.
    Scrapes the URL, extracts property data, and scores it.
    Uses 1 credit.
    """
    if current_user.credits < 1:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please purchase more credits."
        )
    
    analyzer = PropertyAnalyzer()
    result = await analyzer.analyze_url(request.url)
    
    if result.get("success"):
        use_credit(db, current_user, 1)
        
        market_comp = result.get("market_comparison", {})
        if isinstance(market_comp, dict):
            market_comp = MarketComparison(**market_comp)
        
        return URLAnalysisResponse(
            success=True,
            source=result.get("source"),
            url=result.get("url"),
            price=result.get("price"),
            currency=result.get("currency"),
            currency_symbol=result.get("currency_symbol"),
            area=result.get("area"),
            bedrooms=result.get("bedrooms"),
            bathrooms=result.get("bathrooms"),
            address=result.get("address"),
            city=result.get("city"),
            state=result.get("state"),
            country=result.get("country"),
            postal_code=result.get("postal_code"),
            latitude=result.get("latitude"),
            longitude=result.get("longitude"),
            price_per_m2=result.get("price_per_m2"),
            deal_score=result.get("deal_score"),
            market_comparison=market_comp
        )
    else:
        return URLAnalysisResponse(
            success=False,
            error=result.get("error", "Failed to analyze URL")
        )

@router.post("/url", response_model=URLAnalysisResponse)
@router.post("/", response_model=AnalysisResponse)
def create_analysis(
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new property analysis based on user requirements.
    Uses 1 credit.
    """
    # Check credits
    if current_user.credits < 1:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please purchase more credits."
        )
    
    # Use the scoring service
    scoring_service = DealScoringService(db)
    results = scoring_service.analyze_user_requirements(
        budget_min=analysis_request.budget_min or 0,
        budget_max=analysis_request.budget_max,
        city=analysis_request.preferred_city or "Dubai",
        property_type=analysis_request.property_type,
        bedrooms_min=analysis_request.bedrooms_min
    )
    
    # Deduct credit
    use_credit(db, current_user, 1)
    
    # Get best property from results
    best_property = results["top_properties"][0] if results["top_properties"] else None
    
    # Save analysis
    analysis = Analysis(
        user_id=current_user.id,
        budget_min=analysis_request.budget_min,
        budget_max=analysis_request.budget_max,
        preferred_city=analysis_request.preferred_city,
        deal_score=best_property["deal_score"] if best_property else 0,
        price_vs_market=best_property["price_vs_market"] if best_property else 0,
        recommendation=best_property["recommendation"] if best_property else "No properties found",
        insights=json.dumps(results["insights"])
    )
    
    if best_property:
        analysis.property_id = best_property["property"].id
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    # Convert top properties to response format
    top_properties = [
        PropertyWithScore(
            id=item["property"].id,
            title=item["property"].title,
            price=item["property"].price,
            area=item["property"].area,
            price_per_m2=item["property"].price_per_m2,
            city=item["property"].city,
            location=item["property"].location,
            district=item["property"].district,
            country=item["property"].country,
            property_type=item["property"].property_type,
            bedrooms=item["property"].bedrooms,
            bathrooms=item["property"].bathrooms,
            latitude=item["property"].latitude,
            longitude=item["property"].longitude,
            image_url=item["property"].image_url,
            created_at=item["property"].created_at,
            deal_score=item["deal_score"],
            price_vs_market=item["price_vs_market"],
            recommendation=item["recommendation"]
        )
        for item in results["top_properties"]
    ]
    
    return AnalysisResponse(
        id=analysis.id,
        deal_score=analysis.deal_score,
        price_vs_market=analysis.price_vs_market,
        recommendation=analysis.recommendation,
        insights=results["insights"],
        top_properties=top_properties,
        created_at=analysis.created_at
    )


@router.get("/history", response_model=List[AnalysisResponse])
def get_analysis_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's analysis history"""
    query = db.query(Analysis).filter(Analysis.user_id == current_user.id)
    query = query.order_by(desc(Analysis.created_at))
    
    offset = (page - 1) * per_page
    analyses = query.offset(offset).limit(per_page).all()
    
    results = []
    for analysis in analyses:
        # Get top properties for this analysis
        property_query = db.query(Property).filter(
            Property.is_active == True,
            Property.city == (analysis.preferred_city or "Dubai")
        ).limit(5).all()
        
        scoring_service = DealScoringService(db)
        top_properties = []
        for prop in property_query:
            score, diff, rec = scoring_service.calculate_deal_score(prop)
            top_properties.append(PropertyWithScore(
                id=prop.id,
                title=prop.title,
                price=prop.price,
                area=prop.area,
                price_per_m2=prop.price_per_m2,
                city=prop.city,
                location=prop.location,
                district=prop.district,
                country=prop.country,
                property_type=prop.property_type,
                bedrooms=prop.bedrooms,
                bathrooms=prop.bathrooms,
                latitude=prop.latitude,
                longitude=prop.longitude,
                image_url=prop.image_url,
                created_at=prop.created_at,
                deal_score=score,
                price_vs_market=diff,
                recommendation=rec
            ))
        
        insights = json.loads(analysis.insights) if analysis.insights else {}
        
        results.append(AnalysisResponse(
            id=analysis.id,
            deal_score=analysis.deal_score,
            price_vs_market=analysis.price_vs_market,
            recommendation=analysis.recommendation,
            insights=insights,
            top_properties=top_properties,
            created_at=analysis.created_at
        ))
    
    return results


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user"""
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(desc(Analysis.created_at)).limit(5).all()
    
    total_analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).count()
    
    top_score = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(desc(Analysis.deal_score)).first()
    
    # Format recent analyses
    recent_analyses = []
    scoring_service = DealScoringService(db)
    
    for analysis in analyses[:5]:
        property_query = db.query(Property).filter(
            Property.is_active == True
        ).limit(3).all()
        
        top_properties = []
        for prop in property_query:
            score, diff, rec = scoring_service.calculate_deal_score(prop)
            top_properties.append(PropertyWithScore(
                id=prop.id, title=prop.title, price=prop.price,
                area=prop.area, price_per_m2=prop.price_per_m2,
                city=prop.city, location=prop.location,
                district=prop.district, country=prop.country,
                property_type=prop.property_type, bedrooms=prop.bedrooms,
                bathrooms=prop.bathrooms, latitude=prop.latitude,
                longitude=prop.longitude, image_url=prop.image_url,
                created_at=prop.created_at, deal_score=score,
                price_vs_market=diff, recommendation=rec
            ))
        
        insights = json.loads(analysis.insights) if analysis.insights else {}
        
        recent_analyses.append(AnalysisResponse(
            id=analysis.id, deal_score=analysis.deal_score,
            price_vs_market=analysis.price_vs_market,
            recommendation=analysis.recommendation, insights=insights,
            top_properties=top_properties, created_at=analysis.created_at
        ))
    
    return DashboardStats(
        total_analyses=total_analyses,
        credits_remaining=current_user.credits,
        top_deal_score=top_score.deal_score if top_score else None,
        recent_analyses=recent_analyses
    )
