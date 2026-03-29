from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models.models import Property, User, Analysis, MarketStats
from app.schemas.schemas import PropertyResponse, PropertyCreate, PropertyWithScore
from app.services.auth import get_current_user, use_credit
from app.services.deal_scorer import DealScoringService, get_deal_insights
import json

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("/countries")
def get_countries(db: Session = Depends(get_db)):
    """Get all available countries with property counts"""
    results = db.query(
        Property.country,
        Property.region,
        func.count(Property.id).label('count')
    ).filter(
        Property.is_active == True
    ).group_by(
        Property.country, Property.region
    ).all()
    
    return [
        {"country": r[0], "region": r[1], "count": r[2]}
        for r in results
    ]


@router.get("/cities")
def get_cities(
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all available cities"""
    query = db.query(
        Property.city,
        Property.country,
        func.count(Property.id).label('count')
    ).filter(Property.is_active == True)
    
    if country:
        query = query.filter(Property.country == country)
    
    results = query.group_by(Property.city, Property.country).all()
    
    return [
        {"city": r[0], "country": r[1], "count": r[2]}
        for r in results
    ]


@router.get("/", response_model=List[PropertyResponse])
def get_properties(
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_area: Optional[float] = Query(None),
    bedrooms: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Property).filter(Property.is_active == True)
    
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if country:
        query = query.filter(Property.country == country)
    if region:
        query = query.filter(Property.region == region)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if min_price:
        query = query.filter(Property.price >= min_price)
    if max_price:
        query = query.filter(Property.price <= max_price)
    if min_area:
        query = query.filter(Property.area >= min_area)
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)
    
    query = query.order_by(desc(Property.created_at))
    offset = (page - 1) * per_page
    
    properties = query.offset(offset).limit(per_page).all()
    return properties


@router.get("/best-deals", response_model=List[PropertyWithScore])
def get_best_deals(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top rated deals based on AI scoring"""
    query = db.query(Property).filter(Property.is_active == True)
    
    if city:
        query = query.filter(Property.city == city)
    elif country:
        query = query.filter(Property.country == country)
    elif region:
        query = query.filter(Property.region == region)
    
    properties = query.all()
    
    scoring_service = DealScoringService(db)
    scored_properties = []
    
    for prop in properties:
        score, diff, rec = scoring_service.calculate_deal_score(prop)
        prop_dict = PropertyWithScore(
            **{k: v for k, v in prop.__dict__.items() if not k.startswith('_')},
            deal_score=score,
            price_vs_market=diff,
            recommendation=rec
        )
        scored_properties.append(prop_dict)
    
    scored_properties.sort(key=lambda x: x.deal_score, reverse=True)
    return scored_properties[:limit]


@router.get("/worldwide-best", response_model=List[PropertyWithScore])
def get_worldwide_best_deals(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get best deals from all countries"""
    properties = db.query(Property).filter(Property.is_active == True).all()
    
    scoring_service = DealScoringService(db)
    scored_properties = []
    
    for prop in properties:
        score, diff, rec = scoring_service.calculate_deal_score(prop)
        prop_dict = PropertyWithScore(
            **{k: v for k, v in prop.__dict__.items() if not k.startswith('_')},
            deal_score=score,
            price_vs_market=diff,
            recommendation=rec
        )
        scored_properties.append(prop_dict)
    
    scored_properties.sort(key=lambda x: x.deal_score, reverse=True)
    return scored_properties[:limit]


@router.get("/{property_id}", response_model=PropertyWithScore)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(
        Property.id == property_id,
        Property.is_active == True
    ).first()
    
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    scoring_service = DealScoringService(db)
    score, diff, rec = scoring_service.calculate_deal_score(prop)
    
    return PropertyWithScore(
        **{k: v for k, v in prop.__dict__.items() if not k.startswith('_')},
        deal_score=score,
        price_vs_market=diff,
        recommendation=rec
    )


@router.post("/", response_model=PropertyResponse)
def create_property(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    price_per_m2 = property_data.price / property_data.area if property_data.area > 0 else 0
    
    new_property = Property(
        **property_data.dict(),
        price_per_m2=price_per_m2
    )
    
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    
    return new_property


@router.get("/{property_id}/analyze")
def analyze_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.credits < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    use_credit(db, current_user, 1)
    insights = get_deal_insights(db, prop)
    
    analysis = Analysis(
        user_id=current_user.id,
        property_id=property_id,
        deal_score=insights["deal_score"],
        price_vs_market=insights["price_vs_market_percent"],
        recommendation=insights["recommendation"],
        insights=json.dumps(insights)
    )
    db.add(analysis)
    db.commit()
    
    return {
        "analysis": insights,
        "credits_remaining": current_user.credits - 1,
        "analysis_id": analysis.id
    }
