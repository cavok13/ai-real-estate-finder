"""
Comparables Finder - Find similar properties for valuation
Open-source alternative to RentCast API
"""

import math
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .data_sources import PropertyRecord


@dataclass
class ComparableProperty:
    """A comparable property for valuation"""
    address: str
    city: str
    state: str
    zip_code: Optional[str]
    
    # Property details
    bedrooms: Optional[float]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    year_built: Optional[int]
    property_type: str
    
    # Sale info
    sale_price: float
    sale_date: Optional[str]
    days_on_market: Optional[int]
    
    # Distance from subject
    distance_miles: float
    
    # Adjustments
    total_adjustment: float
    adjusted_price: float
    
    # Source
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "squareFeet": self.square_feet,
            "yearBuilt": self.year_built,
            "propertyType": self.property_type,
            "salePrice": self.sale_price,
            "saleDate": self.sale_date,
            "daysOnMarket": self.days_on_market,
            "distanceMiles": round(self.distance_miles, 2),
            "totalAdjustment": round(self.total_adjustment, 0),
            "adjustedPrice": round(self.adjusted_price, 0),
            "source": self.source,
            "pricePerSqFt": round(self.sale_price / self.square_feet, 2) if self.square_feet else None,
        }


class ComparablesFinder:
    """
    Find comparable properties for AVM and valuation.
    
    This service finds properties similar to a subject property
    to use in automated valuations.
    """
    
    # Adjustment values (in dollars or percentages)
    ADJUSTMENTS = {
        "bedroom": {
            "per_bedroom": 5000,  # Each bedroom less = -$5000
        },
        "bathroom": {
            "per_bathroom": 3000,  # Each bathroom less = -$3000
        },
        "square_feet": {
            "per_sqft": 100,  # Per square foot difference
        },
        "year_built": {
            "per_year": 500,  # Each year newer = +$500
        },
        "lot_size": {
            "per_sqft": 10,  # Per sqft of lot difference
        },
        "distance": {
            "max_miles": 1.0,  # Maximum distance for comps
            "discount_per_mile": 0.02,  # 2% discount per mile
        },
    }
    
    def __init__(self):
        self.min_comparables = 3
        self.max_comparables = 10
    
    async def find_comparables(
        self,
        property_record: PropertyRecord,
        radius_miles: float = 1.0,
        limit: int = 10,
        sold_within_days: int = 365,
    ) -> List[ComparableProperty]:
        """
        Find comparable properties.
        
        Args:
            property_record: Subject property
            radius_miles: Search radius
            limit: Maximum number of comparables
            sold_within_days: Only properties sold within this period
            
        Returns:
            List of ComparableProperty objects
        """
        if not property_record.latitude or not property_record.longitude:
            return []
        
        # Search our database for nearby properties
        comparables = await self._search_local_database(
            lat=property_record.latitude,
            lon=property_record.longitude,
            radius_miles=radius_miles,
            sold_within_days=sold_within_days,
            limit=limit * 2,  # Get extra to filter
        )
        
        # Calculate adjustments and sort
        adjusted_comps = []
        for comp in comparables:
            adjustment = self._calculate_adjustment(property_record, comp)
            adjusted_price = comp.sale_price + adjustment
            
            adjusted_comp = ComparableProperty(
                address=comp.address,
                city=comp.city,
                state=comp.state,
                zip_code=comp.zip_code,
                bedrooms=comp.bedrooms,
                bathrooms=comp.bathrooms,
                square_feet=comp.square_feet,
                year_built=comp.year_built,
                property_type=comp.property_type,
                sale_price=comp.sale_price,
                sale_date=comp.last_sale_date,
                days_on_market=self._calculate_days_on_market(comp.last_sale_date),
                distance_miles=self._calculate_distance(
                    property_record.latitude,
                    property_record.longitude,
                    comp.latitude,
                    comp.longitude,
                ),
                total_adjustment=adjustment,
                adjusted_price=adjusted_price,
                source=comp.data_source,
            )
            adjusted_comps.append(adjusted_comp)
        
        # Sort by adjusted price similarity and distance
        subject_value = property_record.last_sale_price or 400000
        adjusted_comps.sort(
            key=lambda x: (
                abs(x.adjusted_price - subject_value) / subject_value,  # Price similarity
                x.distance_miles,  # Then by distance
            )
        )
        
        return adjusted_comps[:limit]
    
    async def _search_local_database(
        self,
        lat: float,
        lon: float,
        radius_miles: float,
        sold_within_days: int,
        limit: int,
    ) -> List[PropertyRecord]:
        """Search our database for nearby sold properties"""
        from app.database import SessionLocal
        from app.models.models import Property
        import math
        
        db = SessionLocal()
        try:
            # Get all properties (simplified - would use spatial queries in production)
            properties = db.query(Property).filter(
                Property.latitude.isnot(None),
                Property.longitude.isnot(None),
                Property.price.isnot(None),
            ).limit(500).all()
            
            # Calculate distance and filter
            results = []
            for prop in properties:
                distance = self._calculate_distance(
                    lat, lon, prop.latitude, prop.longitude
                )
                
                if distance <= radius_miles:
                    record = PropertyRecord(
                        address=prop.address or prop.location or "",
                        city=prop.city,
                        state=prop.state,
                        zip_code=prop.postal_code,
                        county=None,
                        latitude=prop.latitude,
                        longitude=prop.longitude,
                        bedrooms=float(prop.bedrooms) if prop.bedrooms else None,
                        bathrooms=float(prop.bathrooms) if prop.bathrooms else None,
                        square_feet=int(prop.area) if prop.area else None,
                        year_built=prop.year_built,
                        property_type=prop.property_type or "single_family",
                        last_sale_price=prop.price,
                        last_sale_date=prop.updated_at.isoformat() if prop.updated_at else None,
                        data_source="ai_deals_finder_database",
                    )
                    record.distance = distance  # Add distance attribute
                    results.append(record)
            
            # Sort by distance
            results.sort(key=lambda x: x.distance)
            return results[:limit]
            
        finally:
            db.close()
    
    def _calculate_adjustment(
        self,
        subject: PropertyRecord,
        comp: PropertyRecord,
    ) -> float:
        """Calculate total adjustment needed for a comparable"""
        total = 0
        
        # Bedroom adjustment
        if subject.bedrooms and comp.bedrooms:
            bed_diff = subject.bedrooms - comp.bedrooms
            total += bed_diff * self.ADJUSTMENTS["bedroom"]["per_bedroom"]
        
        # Bathroom adjustment
        if subject.bathrooms and comp.bathrooms:
            bath_diff = subject.bathrooms - comp.bathrooms
            total += bath_diff * self.ADJUSTMENTS["bathroom"]["per_bathroom"]
        
        # Square footage adjustment
        if subject.square_feet and comp.square_feet:
            sqft_diff = subject.square_feet - comp.square_feet
            total += sqft_diff * self.ADJUSTMENTS["square_feet"]["per_sqft"]
        
        # Year built adjustment
        if subject.year_built and comp.year_built:
            year_diff = subject.year_built - comp.year_built
            total += year_diff * self.ADJUSTMENTS["year_built"]["per_year"]
        
        # Distance adjustment (comp properties farther away are less reliable)
        if hasattr(comp, 'distance'):
            distance = comp.distance
            distance_penalty = distance * self.ADJUSTMENTS["distance"]["discount_per_mile"] * comp.last_sale_price
            total -= distance_penalty
        
        return total
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_days_on_market(self, sale_date_str: Optional[str]) -> Optional[int]:
        """Calculate days on market from sale date"""
        if not sale_date_str:
            return None
        
        try:
            if isinstance(sale_date_str, str):
                sale_date = datetime.fromisoformat(sale_date_str.replace("Z", "+00:00"))
            else:
                sale_date = sale_date_str
            
            # Assume listed 30 days before sale (average)
            listed_date = sale_date - timedelta(days=30)
            return (sale_date - listed_date).days
        except:
            return None
    
    def get_comparable_analysis(
        self,
        subject: PropertyRecord,
        comparables: List[ComparableProperty],
    ) -> Dict[str, Any]:
        """
        Generate a summary analysis of comparables.
        
        Args:
            subject: Subject property
            comparables: List of comparable properties
            
        Returns:
            Analysis summary dictionary
        """
        if not comparables:
            return {
                "status": "insufficient_data",
                "message": "Not enough comparable properties found",
                "comparableCount": 0,
            }
        
        prices = [c.sale_price for c in comparables]
        adjusted_prices = [c.adjusted_price for c in comparables]
        sqft_prices = [c.sale_price / c.square_feet for c in comparables if c.square_feet]
        
        subject_price = subject.last_sale_price or (sum(prices) / len(prices))
        
        return {
            "status": "success",
            "comparableCount": len(comparables),
            "subjectProperty": {
                "address": subject.address,
                "bedrooms": subject.bedrooms,
                "bathrooms": subject.bathrooms,
                "squareFeet": subject.square_feet,
                "estimatedValue": subject_price,
            },
            "comparableSummary": {
                "lowPrice": min(prices),
                "highPrice": max(prices),
                "averagePrice": sum(prices) / len(prices),
                "medianPrice": sorted(prices)[len(prices) // 2],
                "lowAdjustedPrice": min(adjusted_prices),
                "highAdjustedPrice": max(adjusted_prices),
                "averageAdjustedPrice": sum(adjusted_prices) / len(adjusted_prices),
            },
            "pricePerSqFt": {
                "low": min(sqft_prices) if sqft_prices else None,
                "high": max(sqft_prices) if sqft_prices else None,
                "average": sum(sqft_prices) / len(sqft_prices) if sqft_prices else None,
            },
            "distanceRange": {
                "closest": min(c.distance_miles for c in comparables),
                "farthest": max(c.distance_miles for c in comparables),
            },
            "recommendation": self._generate_recommendation(subject_price, adjusted_prices),
        }
    
    def _generate_recommendation(
        self,
        subject_value: float,
        adjusted_prices: List[float],
    ) -> str:
        """Generate a recommendation based on comparable analysis"""
        avg_adjusted = sum(adjusted_prices) / len(adjusted_prices)
        
        if not subject_value:
            return "insufficient_data"
        
        ratio = subject_value / avg_adjusted if avg_adjusted else 1
        
        if ratio < 0.90:
            return "undervalued"
        elif ratio > 1.10:
            return "overvalued"
        else:
            return "fairly_valued"
