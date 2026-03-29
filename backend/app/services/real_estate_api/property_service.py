"""
Property Service - Main API for property lookups
Open-source alternative to RentCast API
"""

from typing import Optional, Dict, Any, List
from dataclasses import asdict

from .data_sources import DataSourceAggregator, PropertyRecord
from .valuation_engine import ValuationEngine, ValuationResult
from .comparables import ComparablesFinder
from .market_analyzer import MarketAnalyzer


class PropertyService:
    """
    Main property service that combines all functionality.
    This is the primary interface for property lookups.
    
    Endpoints mimic RentCast API structure:
    - /property - Get property details
    - /property/valuation - Get automated valuation
    - /property/comps - Get comparables
    - /property/market - Get market data
    """
    
    def __init__(self):
        self.data_aggregator = DataSourceAggregator()
        self.valuation_engine = ValuationEngine()
        self.comparables_finder = ComparablesFinder()
        self.market_analyzer = MarketAnalyzer()
    
    async def get_property(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        property_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get property details by address or ID.
        
        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: ZIP/Postal code
            property_id: Internal property ID (from our database)
            
        Returns:
            Property record as dictionary or None
        """
        # First try by internal ID
        if property_id:
            from app.database import SessionLocal
            from app.models.models import Property
            
            db = SessionLocal()
            try:
                prop = db.query(Property).filter(Property.id == property_id).first()
                if prop:
                    return self._property_to_record(prop).to_dict()
            finally:
                db.close()
        
        # Then try by address
        if address and city and state:
            record = await self.data_aggregator.get_property_by_address(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
            )
            return record.to_dict() if record else None
        
        return None
    
    async def get_valuation(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        property_id: Optional[int] = None,
        include_comparables: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get automated property valuation (AVM).
        
        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: ZIP/Postal code
            property_id: Internal property ID
            include_comparables: Whether to include comparable sales
            
        Returns:
            Valuation result with estimate, range, and confidence
        """
        # Get property record
        property_record = await self.get_property(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            property_id=property_id,
        )
        
        if not property_record:
            return None
        
        # Convert dict back to PropertyRecord
        record = PropertyRecord(**{
            k: v for k, v in property_record.items() 
            if k in PropertyRecord.__dataclass_fields__
        })
        
        # Get comparables if requested
        comparables = []
        if include_comparables and record.latitude and record.longitude:
            comp_results = await self.comparables_finder.find_comparables(
                property_record=record,
                limit=5,
            )
            comparables = [c.to_dict() for c in comp_results]
        
        # Calculate valuation
        valuation = self.valuation_engine.calculate_valuation(
            property_record=record,
            comparables=comparables,
        )
        
        return valuation.to_dict()
    
    async def get_comparables(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        property_id: Optional[int] = None,
        radius_miles: float = 1.0,
        limit: int = 10,
        sold_within_days: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Find comparable properties.
        
        Args:
            address: Subject property address
            city: City
            state: State
            zip_code: ZIP code
            property_id: Internal property ID
            radius_miles: Search radius in miles
            limit: Maximum number of comparables to return
            sold_within_days: Only include properties sold within this period
            
        Returns:
            List of comparable property records
        """
        # Get subject property
        subject = await self.get_property(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            property_id=property_id,
        )
        
        if not subject:
            return []
        
        record = PropertyRecord(**{
            k: v for k, v in subject.items()
            if k in PropertyRecord.__dataclass_fields__
        })
        
        comps = await self.comparables_finder.find_comparables(
            property_record=record,
            radius_miles=radius_miles,
            limit=limit,
            sold_within_days=sold_within_days,
        )
        
        return [c.to_dict() for c in comps]
    
    async def get_market_rent(
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
        Get market rent estimate for a property type.
        
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
        return await self.market_analyzer.get_rent_estimate(
            city=city,
            state=state,
            zip_code=zip_code,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
        )
    
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
            zip_code: ZIP code
            county: County name
            property_type: Property type filter
            
        Returns:
            Market data including prices, rents, trends, etc.
        """
        return await self.market_analyzer.get_market_data(
            city=city,
            state=state,
            zip_code=zip_code,
            county=county,
            property_type=property_type,
        )
    
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
            School data including ratings, districts, etc.
        """
        return await self.market_analyzer.get_school_data(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
        )
    
    async def search_properties(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        county: Optional[str] = None,
        property_type: Optional[str] = None,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        min_baths: Optional[float] = None,
        max_baths: Optional[float] = None,
        min_sqft: Optional[int] = None,
        max_sqft: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search for properties matching criteria.
        
        Args:
            city: City filter
            state: State filter
            zip_code: ZIP code filter
            county: County filter
            property_type: Property type filter
            min_beds/max_beds: Bedroom range
            min_baths/max_baths: Bathroom range
            min_sqft/max_sqft: Square footage range
            min_price/max_price: Price range
            min_year/max_year: Year built range
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of property records
        """
        records = await self.data_aggregator.search_properties(
            city=city,
            state=state,
            zip_code=zip_code,
            county=county,
            property_type=property_type,
            min_beds=min_beds,
            max_beds=max_beds,
            min_baths=min_baths,
            max_baths=max_baths,
            min_sqft=min_sqft,
            max_sqft=max_sqft,
            min_year=min_year,
            max_year=max_year,
            limit=limit,
            offset=offset,
        )
        
        # Apply price filters
        if min_price or max_price:
            filtered = []
            for record in records:
                price = record.last_sale_price
                if price:
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue
                filtered.append(record)
            records = filtered
        
        return [r.to_dict() for r in records]
    
    def calculate_investment(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        purchase_price: Optional[float] = None,
        down_payment_pct: float = 20,
        interest_rate: float = 7.0,
        loan_term_years: int = 30,
        monthly_rent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate investment metrics for a property.
        
        Args:
            address: Property address
            city: City
            state: State
            zip_code: ZIP code
            purchase_price: Optional purchase price (uses valuation if not provided)
            down_payment_pct: Down payment percentage
            interest_rate: Annual interest rate
            loan_term_years: Loan term
            monthly_rent: Expected monthly rent
            
        Returns:
            Investment metrics including cash flow, cap rate, etc.
        """
        # This would need valuation data - simplified for now
        # In production, this would call get_valuation first
        
        from .valuation_engine import ValuationResult
        
        # Create placeholder valuation
        placeholder = ValuationResult(
            address=address,
            city=city,
            state=state,
            avm_estimate=purchase_price or 400000,
            avm_low=purchase_price * 0.9 if purchase_price else 360000,
            avm_high=purchase_price * 1.1 if purchase_price else 440000,
            confidence=0.7,
            rent_estimate=monthly_rent,
        )
        
        return self.valuation_engine.calculate_investment_metrics(
            valuation=placeholder,
            purchase_price=purchase_price,
            down_payment_pct=down_payment_pct,
            interest_rate=interest_rate,
            loan_term_years=loan_term_years,
            monthly_rent=monthly_rent,
        )
    
    def _property_to_record(self, prop: "Property") -> PropertyRecord:
        """Convert database Property to PropertyRecord"""
        return PropertyRecord(
            address=prop.address or prop.location or "",
            city=prop.city,
            state=prop.state,
            zip_code=prop.postal_code,
            country=prop.country,
            property_type=prop.property_type or "single_family",
            bedrooms=float(prop.bedrooms) if prop.bedrooms else None,
            bathrooms=float(prop.bathrooms) if prop.bathrooms else None,
            square_feet=int(prop.area) if prop.area else None,
            year_built=prop.year_built,
            latitude=prop.latitude,
            longitude=prop.longitude,
            data_source="ai_deals_finder_database",
            last_sale_price=prop.price,
        )
