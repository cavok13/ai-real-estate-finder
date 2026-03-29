from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional, Tuple
from app.models.models import Property, MarketStats
from app.config import settings


def mean(values: List[float]) -> float:
    """Calculate mean of a list"""
    return sum(values) / len(values) if values else 0


class DealScoringService:
    """
    AI-powered deal scoring algorithm.
    
    The algorithm calculates a "deal score" (0-100) based on:
    1. Price per square meter vs area average
    2. Normalization across different areas
    3. Additional factors (bedrooms, location quality)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.market_stats = self._load_market_stats()
    
    def _load_market_stats(self) -> Dict:
        """Load pre-calculated market statistics"""
        stats = self.db.query(MarketStats).all()
        return {
            (s.city, s.district, s.property_type): s for s in stats
        }
    
    def calculate_price_per_m2(self, price: float, area: float) -> float:
        """Calculate price per square meter"""
        if area <= 0:
            return 0
        return price / area
    
    def get_area_average(self, city: str, district: Optional[str] = None, 
                        property_type: Optional[str] = None) -> float:
        """Get average price per m2 for an area"""
        key = (city, district, property_type)
        if key in self.market_stats:
            return self.market_stats[key].avg_price_per_m2
        
        city_stats = [v for k, v in self.market_stats.items() if k[0] == city]
        if city_stats:
            return sum(s.avg_price_per_m2 for s in city_stats) / len(city_stats)
        
        query = self.db.query(func.avg(Property.price_per_m2)).filter(
            Property.city == city,
            Property.is_active == True
        )
        if district:
            query = query.filter(Property.district == district)
        if property_type:
            query = query.filter(Property.property_type == property_type)
        
        result = query.scalar()
        return result if result else 15000
    
    def calculate_deal_score(self, prop: Property) -> Tuple[float, float, str]:
        """
        Calculate deal score for a property.
        """
        if not prop.price_per_m2:
            prop.price_per_m2 = self.calculate_price_per_m2(prop.price, prop.area)
        
        avg_price = self.get_area_average(prop.city, prop.district, prop.property_type)
        price_diff_pct = ((prop.price_per_m2 - avg_price) / avg_price) * 100
        
        if price_diff_pct <= -50:
            base_score = 100
        elif price_diff_pct <= -30:
            base_score = 90 + (30 - abs(price_diff_pct)) / 2
        elif price_diff_pct <= -15:
            base_score = 75 + (30 - abs(price_diff_pct)) / 1.5
        elif price_diff_pct <= 0:
            base_score = 60 + abs(price_diff_pct) * 2
        elif price_diff_pct <= 15:
            base_score = 50 - price_diff_pct
        else:
            base_score = max(0, 35 - price_diff_pct)
        
        if prop.bedrooms and prop.bedrooms > 0:
            value_bonus = min(10, (prop.area / prop.bedrooms) / 50)
            base_score = min(100, base_score + value_bonus)
        
        if base_score >= 80:
            recommendation = "EXCELLENT DEAL! This property is significantly undervalued."
        elif base_score >= 60:
            recommendation = "GOOD DEAL - Worth considering."
        elif base_score >= 40:
            recommendation = "FAIR PRICE - Comparable to market."
        else:
            recommendation = "ABOVE MARKET - Consider negotiating."
        
        return round(base_score, 1), round(price_diff_pct, 1), recommendation
    
    def analyze_user_requirements(self, budget_min: float, budget_max: float,
                                   city: str, property_type: Optional[str] = None,
                                   bedrooms_min: Optional[int] = None) -> Dict:
        """Analyze user requirements and find best matching properties."""
        query = self.db.query(Property).filter(
            Property.city == city,
            Property.is_active == True,
            Property.price >= budget_min
        )
        
        if budget_max:
            query = query.filter(Property.price <= budget_max)
        if property_type:
            query = query.filter(Property.property_type == property_type)
        if bedrooms_min:
            query = query.filter(Property.bedrooms >= bedrooms_min)
        
        properties = query.all()
        
        scored_properties = []
        for prop in properties:
            score, diff, rec = self.calculate_deal_score(prop)
            scored_properties.append({
                "property": prop,
                "deal_score": score,
                "price_vs_market": diff,
                "recommendation": rec
            })
        
        scored_properties.sort(key=lambda x: x["deal_score"], reverse=True)
        top_deals = scored_properties[:settings.TOP_DEALS_COUNT]
        
        prices = [p["property"].price for p in scored_properties]
        avg_score = mean([p["deal_score"] for p in scored_properties]) if scored_properties else 0
        best_deal = scored_properties[0] if scored_properties else None
        
        insights = {
            "total_properties_found": len(scored_properties),
            "market_average_score": round(avg_score, 1),
            "best_deal_score": best_deal["deal_score"] if best_deal else 0,
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
            },
            "area_insights": self._generate_area_insights(city, scored_properties)
        }
        
        return {
            "top_properties": top_deals,
            "all_properties_count": len(scored_properties),
            "insights": insights,
            "market_average_price_per_m2": self.get_area_average(city)
        }
    
    def _generate_area_insights(self, city: str, scored_properties: List[Dict]) -> List[str]:
        """Generate human-readable insights about the area"""
        insights = []
        
        if not scored_properties:
            return ["No properties found in this area."]
        
        prices = [p["property"].price for p in scored_properties]
        areas = [p["property"].area for p in scored_properties]
        
        avg_price = mean(prices)
        avg_area = mean(areas)
        
        insights.append(f"Average property price in {city}: AED {avg_price:,.0f}")
        insights.append(f"Average property size: {avg_area:,.0f} sqm")
        
        areas_dict = {}
        for p in scored_properties:
            district = p["property"].district or "Unknown"
            if district not in areas_dict:
                areas_dict[district] = []
            areas_dict[district].append(p)
        
        if len(areas_dict) > 1:
            area_avg_scores = {
                district: mean([p["deal_score"] for p in props])
                for district, props in areas_dict.items()
            }
            best_area = max(area_avg_scores, key=area_avg_scores.get)
            insights.append(f"Best value district: {best_area} (avg score: {area_avg_scores[best_area]:.1f})")
        
        return insights


def get_deal_insights(db: Session, prop: Property) -> Dict:
    """Quick function to get deal insights for a single property"""
    service = DealScoringService(db)
    score, diff, rec = service.calculate_deal_score(prop)
    avg = service.get_area_average(prop.city, prop.district, prop.property_type)
    
    undervalued_pct = abs(diff) if diff < 0 else 0
    
    return {
        "deal_score": score,
        "price_vs_market_percent": diff,
        "recommendation": rec,
        "market_average_price_per_m2": round(avg, 2),
        "property_price_per_m2": round(prop.price_per_m2, 2) if prop.price_per_m2 else 0,
        "potential_savings": round((avg - prop.price_per_m2) * prop.area, 2) if prop.price_per_m2 else 0,
        "undervalued_by_percent": round(undervalued_pct, 1),
        "analysis": f"This property is priced {abs(diff):.1f}% {'below' if diff < 0 else 'above'} the {prop.city} market average."
    }
