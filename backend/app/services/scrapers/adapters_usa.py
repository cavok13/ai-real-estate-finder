"""
USA Property Scrapers - Zillow, Redfin, Realtor.com
Uses pyzill library for Zillow, custom implementations for others.
"""

import re
import asyncio
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import pyzill
    PYZILL_AVAILABLE = True
except ImportError:
    PYZILL_AVAILABLE = False


@dataclass
class USPropertyData:
    """Standardized US property data"""
    source: str
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    area_sqft: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    year_built: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    description: Optional[str] = None
    features: Optional[list] = None
    photos: Optional[list] = None
    listing_status: str = "active"
    price_history: Optional[list] = None


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class ZillowScraper:
    """Zillow scraper using pyzill library."""
    
    def __init__(self):
        self.source = "Zillow"
    
    async def scrape(self, url: str) -> Optional[USPropertyData]:
        """Scrape property from Zillow URL."""
        if not PYZILL_AVAILABLE:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, pyzill.get_from_url, url)
            
            if not data:
                return None
            
            addr = data.get("address", {})
            
            return USPropertyData(
                source=self.source,
                url=url,
                title=data.get("streetAddress"),
                price=data.get("price"),
                currency="USD",
                area_sqft=data.get("livingArea"),
                bedrooms=data.get("bedrooms"),
                bathrooms=data.get("bathrooms"),
                property_type=data.get("homeType"),
                year_built=data.get("yearBuilt"),
                city=addr.get("city") or data.get("city"),
                state=addr.get("state") or data.get("state"),
                zip_code=addr.get("zipcode") or data.get("zipcode"),
                address=data.get("streetAddress"),
                lat=data.get("latitude"),
                lng=data.get("longitude"),
                description=data.get("description"),
                photos=data.get("photoGallery", {}).get("photos", [])[:5] if data.get("photoGallery") else None,
                features=data.get("resoFacts", {}),
            )
        except Exception as e:
            print(f"Zillow scrape error: {e}")
            return None


class RedfinScraper:
    """Redfin scraper."""
    
    def __init__(self):
        self.source = "Redfin"
        self.base_url = "https://www.redfin.com"
    
    async def scrape(self, url: str) -> Optional[USPropertyData]:
        """Scrape property from Redfin URL."""
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                html = response.text
                
                # Extract JSON data from page
                json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
                
                if json_match:
                    import json
                    data = json.loads(json_match.group(1))
                    
                    # Parse property data from JSON
                    property_data = data.get("property", {}).get("currentListing", {})
                    
                    address_info = property_data.get("address", {})
                    
                    return USPropertyData(
                        source=self.source,
                        url=url,
                        title=property_data.get("name"),
                        price=property_data.get("price"),
                        currency="USD",
                        area_sqft=property_data.get("sqft"),
                        bedrooms=property_data.get("beds"),
                        bathrooms=property_data.get("baths"),
                        property_type=property_data.get("propertyType"),
                        year_built=property_data.get("yearBuilt"),
                        city=address_info.get("city"),
                        state=address_info.get("state"),
                        zip_code=address_info.get("zip"),
                        address=address_info.get("full"),
                        lat=property_data.get("latLong", {}).get("latitude"),
                        lng=property_data.get("latLong", {}).get("longitude"),
                    )
                
                # Fallback: parse HTML
                return self._parse_html(html, url)
                
        except Exception as e:
            print(f"Redfin scrape error: {e}")
            return None
    
    def _parse_html(self, html: str, url: str) -> Optional[USPropertyData]:
        """Fallback HTML parsing for Redfin."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract price
        price_text = soup.find("div", {"class": "price-section"})
        price = None
        if price_text:
            price_match = re.search(r"[\$]([0-9,]+)", price_text.text)
            if price_match:
                price = float(price_match.group(1).replace(",", ""))
        
        # Extract beds/baths
        beds = baths = None
        beds_text = soup.find("div", {"key": "beds"})
        if beds_text:
            beds = int(re.search(r"(\d+)", beds_text.text).group(1))
        
        baths_text = soup.find("div", {"key": "baths"})
        if baths_text:
            baths = int(re.search(r"(\d+)", baths_text.text).group(1))
        
        return USPropertyData(
            source=self.source,
            url=url,
            price=price,
            bedrooms=beds,
            bathrooms=baths,
        )


class RealtorScraper:
    """Realtor.com scraper."""
    
    def __init__(self):
        self.source = "Realtor.com"
        self.base_url = "https://www.realtor.com"
    
    async def scrape(self, url: str) -> Optional[USPropertyData]:
        """Scrape property from Realtor.com URL."""
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                html = response.text
                
                # Look for JSON-LD data
                json_match = re.search(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    html,
                    re.DOTALL
                )
                
                if json_match:
                    import json
                    data = json.loads(json_match.group(1))
                    
                    if isinstance(data, dict):
                        address = data.get("address", {})
                        
                        return USPropertyData(
                            source=self.source,
                            url=url,
                            title=data.get("name"),
                            price=data.get("offers", {}).get("price"),
                            currency="USD",
                            area_sqft=data.get("floorSize", {}).get("value"),
                            bedrooms=data.get("numberOfBedrooms"),
                            bathrooms=data.get("numberOfBathrooms"),
                            property_type=data.get("propertyType"),
                            year_built=data.get("yearBuilt"),
                            city=address.get("addressLocality"),
                            state=address.get("addressRegion"),
                            zip_code=address.get("postalCode"),
                            address=address.get("streetAddress"),
                            description=data.get("description"),
                        )
                
                # Fallback parsing
                return self._parse_html(html, url)
                
        except Exception as e:
            print(f"Realtor scrape error: {e}")
            return None
    
    def _parse_html(self, html: str, url: str) -> Optional[USPropertyData]:
        """Fallback HTML parsing for Realtor.com."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Price
        price_elem = soup.find("span", {"data-testid": "price"})
        price = None
        if price_elem:
            price_match = re.search(r"[\$]([0-9,]+)", price_elem.text)
            if price_match:
                price = float(price_match.group(1).replace(",", ""))
        
        # Beds
        beds = None
        beds_elem = soup.find("span", {"data-testid": "bed"})
        if beds_elem:
            beds = int(re.search(r"(\d+)", beds_elem.text).group(1))
        
        # Baths
        baths = None
        baths_elem = soup.find("span", {"data-testid": "bath"})
        if baths_elem:
            baths = int(re.search(r"(\d+)", baths_elem.text).group(1))
        
        # Sqft
        sqft = None
        sqft_elem = soup.find("span", {"data-testid": "sqft"})
        if sqft_elem:
            sqft = float(re.search(r"([0-9,]+)", sqft_elem.text).group(1).replace(",", ""))
        
        return USPropertyData(
            source=self.source,
            url=url,
            price=price,
            area_sqft=sqft,
            bedrooms=beds,
            bathrooms=baths,
        )


class USPropertyAggregator:
    """Aggregate property data from multiple US sources."""
    
    def __init__(self):
        self.scrapers = {
            "zillow": ZillowScraper(),
            "redfin": RedfinScraper(),
            "realtor": RealtorScraper(),
        }
    
    def detect_source(self, url: str) -> str:
        """Detect which scraper to use based on URL."""
        url_lower = url.lower()
        if "zillow" in url_lower:
            return "zillow"
        elif "redfin" in url_lower:
            return "redfin"
        elif "realtor" in url_lower:
            return "realtor"
        return "zillow"  # Default
    
    async def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape property data from URL."""
        source = self.detect_source(url)
        scraper = self.scrapers.get(source)
        
        if not scraper:
            return None
        
        result = await scraper.scrape(url)
        
        if result:
            return {
                "source": result.source,
                "url": result.url,
                "title": result.title,
                "price": result.price,
                "currency": result.currency,
                "area_sqft": result.area_sqft,
                "bedrooms": result.bedrooms,
                "bathrooms": result.bathrooms,
                "property_type": result.property_type,
                "year_built": result.year_built,
                "city": result.city,
                "state": result.state,
                "zip_code": result.zip_code,
                "address": result.address,
                "latitude": result.lat,
                "longitude": result.lng,
                "description": result.description,
                "features": result.features,
                "photos": result.photos,
            }
        
        return None
    
    async def scrape_multi(self, urls: list) -> list:
        """Scrape multiple URLs concurrently."""
        tasks = [self.scrape(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r and not isinstance(r, Exception)]


us_scraper = USPropertyAggregator()
