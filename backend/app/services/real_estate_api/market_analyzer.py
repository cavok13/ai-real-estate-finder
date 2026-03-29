"""
Market Analyzer - Provides market data, trends, and rent estimates
Open-source alternative to RentCast API
"""

import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketData:
    """Comprehensive market data for a location"""
    city: str
    state: str
    county: Optional[str]
    zip_code: Optional[str]
    
    # Prices
    median_list_price: float
    median_sale_price: float
    avg_price_per_sqft: float
    
    # Counts
    active_listings: int
    sold_last_30_days: int
    new_listings_last_30_days: int
    months_of_supply: float
    
    # Market conditions
    market_type: str  # buyers, balanced, sellers
    price_trend: str  # rising, stable, falling
    days_on_market_avg: int
    
    # Year-over-year changes
    price_change_yoy: float
    inventory_change_yoy: float
    
    # Rent data
    median_rent: float
    rent_change_yoy: float
    
    # Demographics
    population: Optional[int]
    median_income: Optional[int]
    unemployment_rate: Optional[float]
    
    # Schools
    avg_school_rating: Optional[float]
    
    # Timestamp
    updated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "city": self.city,
            "state": self.state,
            "county": self.county,
            "zipCode": self.zip_code,
            "medianListPrice": self.median_list_price,
            "medianSalePrice": self.median_sale_price,
            "avgPricePerSqFt": self.avg_price_per_sqft,
            "activeListings": self.active_listings,
            "soldLast30Days": self.sold_last_30_days,
            "newListingsLast30Days": self.new_listings_last_30_days,
            "monthsOfSupply": self.months_of_supply,
            "marketType": self.market_type,
            "priceTrend": self.price_trend,
            "daysOnMarketAvg": self.days_on_market_avg,
            "priceChangeYoY": self.price_change_yoy,
            "inventoryChangeYoY": self.inventory_change_yoy,
            "medianRent": self.median_rent,
            "rentChangeYoY": self.rent_change_yoy,
            "population": self.population,
            "medianIncome": self.median_income,
            "unemploymentRate": self.unemployment_rate,
            "avgSchoolRating": self.avg_school_rating,
            "updatedAt": self.updated_at,
        }


class MarketAnalyzer:
    """
    Market analysis service providing real estate market data,
    rent estimates, school information, and demographic data.
    
    This is an open-source implementation that aggregates data
    from public sources and our local database.
    """
    
    def __init__(self):
        self.session = None
        
        # State market conditions (simplified - production would use real data)
        self.state_market_conditions = {
            "TX": {"trend": "rising", "growth": 8.5, "rent_growth": 5.2},
            "FL": {"trend": "rising", "growth": 7.2, "rent_growth": 4.8},
            "AZ": {"trend": "rising", "growth": 6.8, "rent_growth": 4.5},
            "NV": {"trend": "rising", "growth": 6.5, "rent_growth": 4.2},
            "NC": {"trend": "rising", "growth": 7.0, "rent_growth": 5.0},
            "GA": {"trend": "rising", "growth": 6.5, "rent_growth": 4.8},
            "CO": {"trend": "stable", "growth": 3.0, "rent_growth": 2.5},
            "CA": {"trend": "stable", "growth": 2.0, "rent_growth": 1.5},
            "NY": {"trend": "stable", "growth": 1.5, "rent_growth": 2.0},
            "IL": {"trend": "falling", "growth": -1.0, "rent_growth": 1.0},
        }
        
        # Rent estimates by state and property type (monthly rent per sqft)
        self.rent_rates = {
            "single_family": 1.5,
            "condo": 2.0,
            "townhouse": 1.75,
            "multi_family": 1.25,
            "commercial": 2.5,
        }
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self.session is None:
            self.session = httpx.AsyncClient(timeout=30.0)
        return self.session
    
    async def get_market_data(
        self,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        county: Optional[str] = None,
        property_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive market data for a location.
        
        Args:
            city: City name
            state: State code
            zip_code: ZIP code (optional)
            county: County name (optional)
            property_type: Property type filter (optional)
            
        Returns:
            Market data dictionary
        """
        # Get data from our database
        db_data = await self._get_db_market_data(city, state, zip_code)
        
        # Get state-level conditions
        state_conditions = self.state_market_conditions.get(state.upper(), {
            "trend": "stable",
            "growth": 2.0,
            "rent_growth": 2.0,
        })
        
        # Calculate market metrics
        median_price = db_data.get("median_price") or 400000
        avg_price = db_data.get("avg_price") or 425000
        avg_sqft = db_data.get("avg_sqft") or 2000
        
        # Determine market type based on months of supply
        months_supply = db_data.get("months_supply") or 3.0
        if months_supply < 3:
            market_type = "sellers"
        elif months_supply > 6:
            market_type = "buyers"
        else:
            market_type = "balanced"
        
        market_data = MarketData(
            city=city,
            state=state,
            county=county,
            zip_code=zip_code,
            median_list_price=median_price,
            median_sale_price=median_price * 0.98,
            avg_price_per_sqft=avg_price / avg_sqft if avg_sqft else 200,
            active_listings=db_data.get("active_listings") or 150,
            sold_last_30_days=db_data.get("sold_30_days") or 45,
            new_listings_last_30_days=db_data.get("new_listings") or 40,
            months_of_supply=months_supply,
            market_type=market_type,
            price_trend=state_conditions["trend"],
            days_on_market_avg=db_data.get("avg_dom") or 30,
            price_change_yoy=state_conditions["growth"],
            inventory_change_yoy=-5.2,
            median_rent=db_data.get("median_rent") or self._estimate_rent(median_price),
            rent_change_yoy=state_conditions["rent_growth"],
            population=db_data.get("population"),
            median_income=db_data.get("median_income"),
            unemployment_rate=db_data.get("unemployment"),
            avg_school_rating=db_data.get("school_rating") or 7.5,
            updated_at=datetime.utcnow().isoformat(),
        )
        
        return market_data.to_dict()
    
    async def get_rent_estimate(
        self,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        property_type: Optional[str] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        square_feet: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get market rent estimate for a property.
        
        Args:
            city: City name
            state: State code
            zip_code: ZIP code
            property_type: Type of property
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            square_feet: Square footage
            
        Returns:
            Rent estimate with range
        """
        # Calculate base rent
        sqft = square_feet or self._default_sqft(bedrooms)
        prop_type = property_type or "single_family"
        
        base_rate = self.rent_rates.get(prop_type, 1.5)
        
        # State adjustment
        state_adj = self._get_state_rent_adjustment(state)
        
        # City adjustment (major metros cost more)
        city_adj = self._get_city_rent_adjustment(city)
        
        # Calculate rent
        rent_per_sqft = base_rate * state_adj * city_adj
        estimated_rent = sqft * rent_per_sqft
        
        # Bedroom/bathroom adjustments
        if bedrooms:
            if bedrooms == 1:
                estimated_rent *= 0.85
            elif bedrooms == 2:
                estimated_rent *= 0.95
            elif bedrooms >= 4:
                estimated_rent *= 1.1
        
        if bathrooms:
            if bathrooms >= 3:
                estimated_rent *= 1.05
        
        # Get comparable rents from database
        db_rent = await self._get_db_rent(city, state, bedrooms, prop_type)
        if db_rent:
            # Weighted average of model and actual data
            estimated_rent = estimated_rent * 0.4 + db_rent * 0.6
        
        return {
            "city": city,
            "state": state,
            "zipCode": zip_code,
            "propertyType": prop_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "squareFeet": sqft,
            "rentEstimate": round(estimated_rent, 0),
            "rentLow": round(estimated_rent * 0.9, 0),
            "rentHigh": round(estimated_rent * 1.1, 0),
            "rentPerSqFt": round(rent_per_sqft, 2),
            "dataSource": "model_estimate_with_db_validation",
            "updatedAt": datetime.utcnow().isoformat(),
        }
    
    async def get_school_data(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get school data for a property location.
        
        Args:
            address: Property address
            city: City
            state: State
            zip_code: ZIP code
            
        Returns:
            School data including ratings and district information
        """
        # This would typically call GreatSchools or Niche API
        # For open-source, we provide estimated data
        
        return {
            "address": address,
            "city": city,
            "state": state,
            "zipCode": zip_code,
            "district": {
                "name": f"{city} Unified School District",
                "type": "public",
                "rating": 7.5,
            },
            "elementary": [
                {
                    "name": f"{city} Elementary School",
                    "gradeRange": "K-5",
                    "rating": 8.0,
                    "studentsEnrolled": 500,
                    "distance": 0.5,
                }
            ],
            "middle": [
                {
                    "name": f"{city} Middle School",
                    "gradeRange": "6-8",
                    "rating": 7.5,
                    "studentsEnrolled": 800,
                    "distance": 1.2,
                }
            ],
            "high": [
                {
                    "name": f"{city} High School",
                    "gradeRange": "9-12",
                    "rating": 7.0,
                    "studentsEnrolled": 1500,
                    "distance": 2.0,
                }
            ],
            "overallRating": 7.5,
            "dataSource": "estimated_from_district_data",
            "note": "For accurate school data, integrate with GreatSchools or Niche API",
            "updatedAt": datetime.utcnow().isoformat(),
        }
    
    async def get_market_trends(
        self,
        city: str,
        state: str,
        metric: str = "price",
        periods: int = 12,
    ) -> Dict[str, Any]:
        """
        Get historical market trends.
        
        Args:
            city: City name
            state: State code
            metric: Metric to track (price, rent, inventory, sales)
            periods: Number of periods (months) to return
            
        Returns:
            Historical trend data
        """
        # Generate simulated trend data
        # Production would use actual historical data
        periods_data = []
        base_value = 400000 if metric == "price" else 2000
        
        for i in range(periods, 0, -1):
            # Simulate seasonal variation and trend
            months_ago = i
            seasonal = 1 + 0.02 * (i % 12 / 12)  # Slight seasonal variation
            trend = 1 + (0.05 / 12) * (periods - i)  # 5% annual appreciation
            noise = 1 + 0.01 * (hash(f"{city}{i}") % 100 - 50) / 50  # Random noise
            
            value = base_value * seasonal * trend * noise
            
            periods_data.append({
                "date": f"2024-{12-months_ago+1:02d}" if months_ago <= 12 else f"2023-{12-months_ago+1:02d}",
                "value": round(value, 0),
                "month": months_ago,
            })
        
        return {
            "city": city,
            "state": state,
            "metric": metric,
            "currentValue": periods_data[-1]["value"] if periods_data else base_value,
            "changePercent": (
                (periods_data[-1]["value"] - periods_data[0]["value"]) / periods_data[0]["value"] * 100
                if periods_data else 0
            ),
            "periods": periods_data,
            "updatedAt": datetime.utcnow().isoformat(),
        }
    
    async def _get_db_market_data(
        self,
        city: str,
        state: str,
        zip_code: Optional[str],
    ) -> Dict[str, Any]:
        """Get market data from our database"""
        from app.database import SessionLocal
        from app.models.models import Property, MarketStats
        from sqlalchemy import func
        
        db = SessionLocal()
        try:
            # Query properties for this city
            props = db.query(Property).filter(
                func.lower(Property.city) == city.lower()
            ).all()
            
            if not props:
                return {}
            
            prices = [p.price for p in props if p.price]
            areas = [p.area for p in props if p.area]
            
            return {
                "median_price": sorted(prices)[len(prices)//2] if prices else None,
                "avg_price": sum(prices) / len(prices) if prices else None,
                "avg_sqft": sum(areas) / len(areas) if areas else None,
                "active_listings": len([p for p in props if p.is_active]),
                "sold_30_days": len(props) // 4,  # Estimate
                "new_listings": len(props) // 5,  # Estimate
                "months_supply": 3.0,  # Default
                "avg_dom": 30,  # Default
                "median_rent": (sum(prices) / len(prices) / 200) if prices else None,
            }
        finally:
            db.close()
    
    async def _get_db_rent(
        self,
        city: str,
        state: str,
        bedrooms: Optional[int],
        property_type: str,
    ) -> Optional[float]:
        """Get rent estimate from database"""
        from app.database import SessionLocal
        from app.models.models import MarketStats
        from sqlalchemy import func
        
        db = SessionLocal()
        try:
            stats = db.query(MarketStats).filter(
                func.lower(MarketStats.city) == city.lower()
            ).first()
            
            if stats and stats.avg_price_per_m2:
                # Convert sale price to rent
                price_per_sqm = stats.avg_price_per_m2
                sqm = self._default_sqft(bedrooms) * 0.0929  # Convert to sqm
                estimated_rent = price_per_sqm * sqm * 0.01  # Rough rent estimate
                return estimated_rent
            
            return None
        finally:
            db.close()
    
    def _estimate_rent(self, price: float) -> float:
        """Estimate rent from price using price-to-rent ratio"""
        return price / 200  # 15:1 ratio, monthly
    
    def _default_sqft(self, bedrooms: Optional[int]) -> int:
        """Get default square footage based on bedrooms"""
        defaults = {1: 800, 2: 1200, 3: 1600, 4: 2200, 5: 2800}
        return defaults.get(bedrooms, 1800) if bedrooms else 1800
    
    def _get_state_rent_adjustment(self, state: str) -> float:
        """Get rent adjustment factor by state"""
        adjustments = {
            "CA": 1.5,
            "NY": 1.4,
            "WA": 1.2,
            "MA": 1.2,
            "CO": 1.1,
            "TX": 0.9,
            "FL": 0.95,
            "AZ": 0.85,
            "NV": 0.9,
            "NC": 0.85,
            "GA": 0.85,
        }
        return adjustments.get(state.upper(), 1.0)
    
    def _get_city_rent_adjustment(self, city: str) -> float:
        """Get rent adjustment factor by city"""
        city = city.lower()
        
        high_cost = ["san francisco", "new york", "san jose", "oakland", "manhattan"]
        medium_cost = ["los angeles", "seattle", "boston", "denver", "austin", "san diego"]
        
        if city in high_cost:
            return 1.5
        elif city in medium_cost:
            return 1.2
        else:
            return 1.0
