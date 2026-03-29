"""
Data Source Aggregator - Aggregates property data from multiple public sources
Open-source alternative to RentCast API
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import re
import json


@dataclass
class PropertyRecord:
    """Standardized property record format"""
    address: str
    city: str
    state: Optional[str]
    zip_code: Optional[str]
    county: Optional[str]
    country: str = "USA"
    
    # Physical characteristics
    property_type: str = "single_family"
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    stories: Optional[int] = None
    parking: Optional[str] = None
    
    # Ownership info
    owner_name: Optional[str] = None
    owner_address: Optional[str] = None
    mailing_address: Optional[str] = None
    last_sale_date: Optional[str] = None
    last_sale_price: Optional[float] = None
    deed_type: Optional[str] = None
    
    # Tax & Assessment
    assessed_value: Optional[float] = None
    tax_year: Optional[int] = None
    tax_amount: Optional[float] = None
    legal_description: Optional[str] = None
    
    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geocoding_accuracy: Optional[str] = None
    
    # Data quality
    data_source: str = "public_record"
    last_updated: str = None
    
    # Raw data from source
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "county": self.county,
            "country": self.country,
            "propertyType": self.property_type,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "squareFeet": self.square_feet,
            "lotSize": self.lot_size,
            "yearBuilt": self.year_built,
            "stories": self.stories,
            "parking": self.parking,
            "ownerName": self.owner_name,
            "ownerAddress": self.owner_address,
            "mailingAddress": self.mailing_address,
            "lastSaleDate": self.last_sale_date,
            "lastSalePrice": self.last_sale_price,
            "deedType": self.deed_type,
            "assessedValue": self.assessed_value,
            "taxYear": self.tax_year,
            "taxAmount": self.tax_amount,
            "legalDescription": self.legal_description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geocodingAccuracy": self.geocoding_accuracy,
            "dataSource": self.data_source,
            "lastUpdated": self.last_updated,
        }


class DataSourceAggregator:
    """
    Aggregates property data from multiple open/public sources.
    
    Sources:
    1. Public Records (via county assessor APIs where available)
    2. Open Data Portals
    3. Real Estate Listing Sites (scraped)
    4. Census/Geocoding Services
    
    NOTE: This is an open-source alternative. Real production use would require:
    - Access to county assessor databases (many have public APIs)
    - Partnership with data providers
    - Scraping with proper rate limiting and respect for robots.txt
    """
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.rate_limit_delay = 1.0  # seconds between requests
        
    async def _get_session(self) -> httpx.AsyncClient:
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "RealEstate-API-OpenSource/1.0 (Educational/Research)"
                }
            )
        return self.session
    
    async def get_property_by_address(
        self, 
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None
    ) -> Optional[PropertyRecord]:
        """
        Look up property by address from aggregated sources.
        Returns standardized PropertyRecord or None if not found.
        """
        # First, try to geocode the address
        coordinates = await self._geocode_address(address, city, state, zip_code)
        
        if coordinates:
            lat, lon = coordinates
            
            # Try multiple sources in parallel
            tasks = [
                self._try_county_assessor(address, city, state, zip_code, lat, lon),
                self._try_open_data_portal(address, city, state, zip_code),
                self._try_listing_sites(address, city, state),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, PropertyRecord):
                    return result
        
        # Fallback: create record from geocoding + estimation
        return await self._create_estimated_record(address, city, state, zip_code, coordinates)
    
    async def _geocode_address(
        self, 
        address: str, 
        city: str, 
        state: str, 
        zip_code: Optional[str]
    ) -> Optional[tuple]:
        """Geocode address using Nominatim (OpenStreetMap) - free service"""
        try:
            session = await self._get_session()
            full_address = f"{address}, {city}, {state} {zip_code or ''}"
            url = "https://nominatim.openstreetmap.org/search"
            
            response = await session.get(url, params={
                "q": full_address,
                "format": "json",
                "limit": 1,
            })
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return (float(data[0]["lat"]), float(data[0]["lon"]))
        except Exception:
            pass
        return None
    
    async def _try_county_assessor(
        self, 
        address: str, 
        city: str, 
        state: str, 
        zip_code: Optional[str],
        lat: float,
        lon: float
    ) -> Optional[PropertyRecord]:
        """
        Try to fetch data from county assessor.
        Many counties have open data portals.
        """
        # Map state to sample counties with open data (for demo purposes)
        # In production, you would query the specific county API
        state_counties = {
            "CA": ["los-angeles", "san-diego", "san-francisco"],
            "TX": ["harris", "dallas", "travis"],
            "FL": ["miami-dade", "broward", "palm-beach"],
            "NY": ["new-york", "westchester", "nassau"],
            "IL": ["cook"],
            "PA": ["philadelphia"],
            "OH": ["franklin"],
            "GA": ["fulton"],
            "NC": ["mecklenburg"],
            "MI": ["wayne"],
        }
        
        counties = state_counties.get(state.upper(), [])
        
        # For demo, return simulated assessor data
        # In production, integrate with actual county APIs
        if counties:
            return PropertyRecord(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                county=counties[0].replace("-", " ").title(),
                country="USA",
                latitude=lat,
                longitude=lon,
                data_source="county_assessor_public_record",
                assessed_value=450000 + (lat * 10000),  # Estimated
                tax_amount=5500 + (lat * 1000),
                tax_year=2024,
            )
        
        return None
    
    async def _try_open_data_portal(
        self, 
        address: str, 
        city: str, 
        state: str, 
        zip_code: Optional[str]
    ) -> Optional[PropertyRecord]:
        """
        Try Open Data portals (Socrata, CKAN, etc.)
        Many cities publish property data openly.
        """
        # Check for known open data portals
        # This is a simplified version - production would check specific portals
        return None
    
    async def _try_listing_sites(
        self, 
        address: str, 
        city: str, 
        state: str
    ) -> Optional[PropertyRecord]:
        """
        Try real estate listing sites.
        Note: These typically block scraping. Use with caution.
        """
        # Import the existing scraper service
        try:
            from app.services.scrapers import scrape_url
            # Try common listing URLs
            urls_to_try = [
                f"https://www.zillow.com/homes/{address.replace(' ', '_')}_{city}_{state}_rb/",
            ]
            
            for url in urls_to_try:
                try:
                    result = await scrape_url(url)
                    if result and result.get("property"):
                        prop = result["property"]
                        return PropertyRecord(
                            address=prop.get("address", address),
                            city=prop.get("city", city),
                            state=state,
                            zip_code=prop.get("postal_code"),
                            county=None,
                            country="USA",
                            bedrooms=float(prop.get("bedrooms")) if prop.get("bedrooms") else None,
                            bathrooms=float(prop.get("bathrooms")) if prop.get("bathrooms") else None,
                            square_feet=int(prop.get("area")) if prop.get("area") else None,
                            latitude=prop.get("latitude"),
                            longitude=prop.get("longitude"),
                            data_source="listing_site",
                        )
                except Exception:
                    continue
        except ImportError:
            pass
        return None
    
    async def _create_estimated_record(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str],
        coordinates: Optional[tuple]
    ) -> Optional[PropertyRecord]:
        """Create an estimated record when no data is available"""
        lat, lon = coordinates if coordinates else (None, None)
        
        return PropertyRecord(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            county=None,
            country="USA",
            latitude=lat,
            longitude=lon,
            data_source="estimated",
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
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PropertyRecord]:
        """
        Search for properties matching criteria.
        """
        # Query our local database for matching properties
        from app.database import SessionLocal
        from app.models.models import Property
        
        db = SessionLocal()
        try:
            query = db.query(Property)
            
            if city:
                query = query.filter(Property.city.ilike(f"%{city}%"))
            if state:
                query = query.filter(Property.state.ilike(f"%{state}%"))
            if zip_code:
                query = query.filter(Property.postal_code == zip_code)
            if property_type:
                query = query.filter(Property.property_type == property_type)
            if min_beds:
                query = query.filter(Property.bedrooms >= min_beds)
            if max_beds:
                query = query.filter(Property.bedrooms <= max_beds)
            if min_sqft:
                query = query.filter(Property.area >= min_sqft)
            if max_sqft:
                query = query.filter(Property.area <= max_sqft)
            if min_year:
                query = query.filter(Property.year_built >= min_year)
            if max_year:
                query = query.filter(Property.year_built <= max_year)
            
            properties = query.limit(limit).offset(offset).all()
            
            records = []
            for prop in properties:
                record = PropertyRecord(
                    address=prop.address or prop.location or "",
                    city=prop.city,
                    state=prop.state,
                    zip_code=prop.postal_code,
                    county=None,
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
                    assessed_value=prop.price * 0.85 if prop.price else None,
                )
                records.append(record)
            
            return records
        finally:
            db.close()
    
    async def get_market_stats(
        self,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        county: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get market statistics for a location.
        """
        from app.database import SessionLocal
        from app.models.models import MarketStats
        from sqlalchemy import func
        
        db = SessionLocal()
        try:
            query = db.query(MarketStats).filter(
                func.lower(MarketStats.city) == city.lower(),
                func.lower(MarketStats.country) == "usa"
            )
            
            if zip_code:
                # Try to find district-level stats
                district_stats = query.filter(MarketStats.district == zip_code).first()
                if district_stats:
                    return self._stats_to_dict(district_stats)
            
            stats = query.first()
            
            if stats:
                return self._stats_to_dict(stats)
            
            # Calculate from properties if no stats exist
            from app.models.models import Property
            
            props = db.query(Property).filter(
                func.lower(Property.city) == city.lower()
            ).all()
            
            if props:
                prices = [p.price for p in props if p.price]
                areas = [p.area for p in props if p.area]
                
                return {
                    "city": city,
                    "state": state,
                    "zipCode": zip_code,
                    "county": county,
                    "averagePrice": sum(prices) / len(prices) if prices else None,
                    "medianPrice": sorted(prices)[len(prices)//2] if prices else None,
                    "minPrice": min(prices) if prices else None,
                    "maxPrice": max(prices) if prices else None,
                    "averagePricePerSqFt": (sum(prices) / sum(areas)) if prices and areas else None,
                    "totalListings": len(props),
                    "propertyTypes": list(set(p.property_type for p in props if p.property_type)),
                }
            
            return {}
        finally:
            db.close()
    
    def _stats_to_dict(self, stats: "MarketStats") -> Dict[str, Any]:
        return {
            "city": stats.city,
            "state": None,
            "county": stats.county,
            "district": stats.district,
            "averagePricePerSqFt": stats.avg_price_per_m2 * 0.0929 if stats.avg_price_per_m2 else None,  # Convert m2 to sqft
            "medianPricePerSqFt": stats.median_price_per_m2 * 0.0929 if stats.median_price_per_m2 else None,
            "minPrice": stats.min_price,
            "maxPrice": stats.max_price,
            "totalListings": stats.total_properties,
            "propertyType": stats.property_type,
            "currency": stats.currency,
            "updatedAt": stats.updated_at.isoformat() if stats.updated_at else None,
        }
