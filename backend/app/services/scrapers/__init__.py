"""
Property Scraper Service
Unified adapter system for scraping property listings from multiple sources
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
import httpx
from urllib.parse import urlparse


@dataclass
class NormalizedProperty:
    """Standardized property data from any source"""
    url: str
    source: str
    price: Optional[float] = None
    currency: str = "USD"
    area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    year_built: Optional[int] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    raw_data: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "source": self.source,
            "price": self.price,
            "currency": self.currency,
            "area": self.area,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "property_type": self.property_type,
            "year_built": self.year_built,
            "description": self.description,
        }


class BaseAdapter:
    """Base class for property adapters"""
    
    def __init__(self):
        self.name = "base"
        self.supported_domains = []
    
    def can_handle(self, url: str) -> bool:
        """Check if this adapter can handle the URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(d in domain for d in self.supported_domains)
    
    async def scrape(self, url: str) -> NormalizedProperty:
        """Scrape and normalize property data"""
        raise NotImplementedError
    
    async def fetch_page(self, url: str) -> str:
        """Fetch HTML page with proper headers"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    
    def extract_number(self, text: str) -> Optional[float]:
        """Extract first number from text"""
        if not text:
            return None
        match = re.search(r"[\d,]+(?:\.\d+)?", text.replace(",", ""))
        if match:
            return float(match.group().replace(",", ""))
        return None


class ZillowAdapter(BaseAdapter):
    """Adapter for Zillow.com"""
    
    def __init__(self):
        super().__init__()
        self.name = "zillow"
        self.supported_domains = ["zillow.com", "zillow.co.uk"]
    
    async def scrape(self, url: str) -> NormalizedProperty:
        html = await self.fetch_page(url)
        
        # Try to extract from JSON-LD first
        data = self._extract_json_ld(html)
        
        if not data:
            data = self._extract_from_html(html)
        
        return NormalizedProperty(
            url=url,
            source="zillow",
            price=data.get("price"),
            currency="USD",
            area=data.get("area"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            postal_code=data.get("postal_code"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            property_type=data.get("property_type"),
            year_built=data.get("year_built"),
        )
    
    def _extract_json_ld(self, html: str) -> Dict[str, Any]:
        """Extract data from JSON-LD scripts"""
        import json
        
        pattern = r'<script[^>]*type="application/ld\+json"[^>]*>([^<]+)</script>'
        matches = re.findall(pattern, html)
        
        for match in matches:
            try:
                data = json.loads(match)
                if data.get("@type") == "Product" or "offers" in data:
                    price = None
                    if "offers" in data:
                        price = self.extract_number(data["offers"].get("price", ""))
                    
                    return {
                        "price": price,
                        "address": data.get("address", {}).get("streetAddress") if isinstance(data.get("address"), dict) else data.get("address"),
                        "city": data.get("address", {}).get("addressLocality") if isinstance(data.get("address"), dict) else None,
                        "state": data.get("address", {}).get("addressRegion") if isinstance(data.get("address"), dict) else None,
                    }
            except:
                continue
        return {}
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        """Fallback extraction from HTML"""
        data = {}
        
        # Price
        price_pattern = r'"price"\s*:\s*(\d+)'
        price_match = re.search(price_pattern, html)
        if price_match:
            data["price"] = int(price_match.group(1))
        
        # Address
        address_pattern = r'"streetAddress"\s*:\s*"([^"]+)"'
        if re.search(address_pattern, html):
            data["address"] = re.search(address_pattern, html).group(1)
        
        # City
        city_pattern = r'"addressLocality"\s*:\s*"([^"]+)"'
        if re.search(city_pattern, html):
            data["city"] = re.search(city_pattern, html).group(1)
        
        # Bedrooms
        beds_pattern = r'"numberOfBedrooms"\s*:\s*(\d+)'
        if re.search(beds_pattern, html):
            data["bedrooms"] = int(re.search(beds_pattern, html).group(1))
        
        # Bathrooms
        baths_pattern = r'"numberOfBathrooms"\s*:\s*(\d+)'
        if re.search(baths_pattern, html):
            data["bathrooms"] = int(re.search(baths_pattern, html).group(1))
        
        # Area
        area_pattern = r'"floorSize"\s*:\s*\{[^}]*"value"\s*:\s*(\d+)'
        if re.search(area_pattern, html):
            data["area"] = float(re.search(area_pattern, html).group(1))
        
        return data


class RealtorAdapter(BaseAdapter):
    """Adapter for Realtor.com"""
    
    def __init__(self):
        super().__init__()
        self.name = "realtor"
        self.supported_domains = ["realtor.com"]
    
    async def scrape(self, url: str) -> NormalizedProperty:
        html = await self.fetch_page(url)
        
        data = self._extract_from_html(html)
        
        return NormalizedProperty(
            url=url,
            source="realtor",
            price=data.get("price"),
            currency="USD",
            area=data.get("area"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            postal_code=data.get("postal_code"),
            property_type=data.get("property_type"),
        )
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        data = {}
        
        # Price
        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})+)', html)
        if price_match:
            data["price"] = self.extract_number(price_match.group())
        
        # Beds
        beds_match = re.search(r'(\d+)\s*bed', html, re.I)
        if beds_match:
            data["bedrooms"] = int(beds_match.group(1))
        
        # Baths
        baths_match = re.search(r'(\d+)\s*bath', html, re.I)
        if baths_match:
            data["bathrooms"] = int(baths_match.group(1))
        
        # Sqft
        sqft_match = re.search(r'([\d,]+)\s*sqft', html, re.I)
        if sqft_match:
            data["area"] = self.extract_number(sqft_match.group())
        
        return data


class RightmoveAdapter(BaseAdapter):
    """Adapter for Rightmove.co.uk"""
    
    def __init__(self):
        super().__init__()
        self.name = "rightmove"
        self.supported_domains = ["rightmove.co.uk"]
    
    async def scrape(self, url: str) -> NormalizedProperty:
        html = await self.fetch_page(url)
        
        data = self._extract_from_html(html)
        
        return NormalizedProperty(
            url=url,
            source="rightmove",
            price=data.get("price"),
            currency="GBP",
            area=data.get("area"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            address=data.get("address"),
            city=data.get("city"),
            property_type=data.get("property_type"),
        )
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        data = {}
        
        # Price
        price_pattern = r'price"\s*:\s*"([^"]+)"'
        if re.search(price_pattern, html):
            price_str = re.search(price_pattern, html).group(1).replace(",", "").replace("£", "")
            data["price"] = self.extract_number(price_str)
        
        # Address
        address_pattern = r'displayAddress"\s*:\s*"([^"]+)"'
        if re.search(address_pattern, html):
            data["address"] = re.search(address_pattern, html).group(1)
        
        # Bedrooms
        beds_pattern = r'bedrooms"\s*:\s*(\d+)'
        if re.search(beds_pattern, html):
            data["bedrooms"] = int(re.search(beds_pattern, html).group(1))
        
        return data


class BayutAdapter(BaseAdapter):
    """Adapter for Bayut.com (UAE)"""
    
    def __init__(self):
        super().__init__()
        self.name = "bayut"
        self.supported_domains = ["bayut.com"]
    
    async def scrape(self, url: str) -> NormalizedProperty:
        html = await self.fetch_page(url)
        
        data = self._extract_from_html(html)
        
        return NormalizedProperty(
            url=url,
            source="bayut",
            price=data.get("price"),
            currency=data.get("currency", "AED"),
            area=data.get("area"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            address=data.get("address"),
            city=data.get("city"),
            property_type=data.get("property_type"),
        )
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        data = {"currency": "AED"}
        
        # Price
        price_pattern = r'<span[^>]*class="[^"]*price[^"]*"[^>]*>([^<]+)</span>'
        if re.search(price_pattern, html, re.I):
            price_text = re.search(price_pattern, html, re.I).group(1)
            data["price"] = self.extract_number(price_text)
        
        # Area
        area_pattern = r'(\d+[\d,]*)\s*sq\s*ft'
        if re.search(area_pattern, html, re.I):
            data["area"] = self.extract_number(re.search(area_pattern, html, re.I).group(1))
        
        # Bedrooms
        beds_pattern = r'<li[^>]*>(\d+)\s*Beds?</li>'
        if re.search(beds_pattern, html, re.I):
            data["bedrooms"] = int(re.search(beds_pattern, html, re.I).group(1))
        
        # Bathrooms
        baths_pattern = r'<li[^>]*>(\d+)\s*Baths?</li>'
        if re.search(baths_pattern, html, re.I):
            data["bathrooms"] = int(re.search(baths_pattern, html, re.I).group(1))
        
        return data


class PropertyFinderAdapter(BaseAdapter):
    """Adapter for PropertyFinder.ae (UAE)"""
    
    def __init__(self):
        super().__init__()
        self.name = "propertyfinder"
        self.supported_domains = ["propertyfinder.ae"]
    
    async def scrape(self, url: str) -> NormalizedProperty:
        html = await self.fetch_page(url)
        
        data = self._extract_from_html(html)
        
        return NormalizedProperty(
            url=url,
            source="propertyfinder",
            price=data.get("price"),
            currency=data.get("currency", "AED"),
            area=data.get("area"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            address=data.get("address"),
            city=data.get("city"),
            property_type=data.get("property_type"),
        )
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        data = {"currency": "AED"}
        
        # Price - try multiple patterns
        price_patterns = [
            r'data-price="([^"]+)"',
            r'"price"\s*:\s*"([^"]+)"',
            r' AED\s*([\d,]+)',
        ]
        for pattern in price_patterns:
            if re.search(pattern, html):
                data["price"] = self.extract_number(re.search(pattern, html).group(1))
                break
        
        return data


class RedfinAdapter(BaseAdapter):
    """Adapter for Redfin.com"""
    
    def __init__(self):
        super().__init__()
        self.name = "redfin"
        self.supported_domains = ["redfin.com"]
    
    async def scrape(self, url: str) -> NormalizedProperty:
        html = await self.fetch_page(url)
        
        data = self._extract_from_html(html)
        
        return NormalizedProperty(
            url=url,
            source="redfin",
            price=data.get("price"),
            currency="USD",
            area=data.get("area"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
        )
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        data = {}
        
        # Price
        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})+)', html)
        if price_match:
            data["price"] = self.extract_number(price_match.group())
        
        return data


class GenericAdapter(BaseAdapter):
    """Fallback adapter for unknown sites"""
    
    def __init__(self):
        super().__init__()
        self.name = "generic"
        self.supported_domains = []
    
    def can_handle(self, url: str) -> bool:
        """Generic adapter handles all URLs"""
        return True
    
    async def scrape(self, url: str) -> NormalizedProperty:
        """Extract what we can from any property page"""
        try:
            html = await self.fetch_page(url)
            parsed = urlparse(url)
            data = self._extract_from_html(html)
            
            return NormalizedProperty(
                url=url,
                source=parsed.netloc,
                price=data.get("price"),
                currency=data.get("currency", "USD"),
                area=data.get("area"),
                bedrooms=data.get("bedrooms"),
                bathrooms=data.get("bathrooms"),
                address=data.get("address"),
                city=data.get("city"),
                property_type=data.get("property_type"),
            )
        except Exception as e:
            return NormalizedProperty(
                url=url,
                source="unknown",
                price=None,
                error=str(e)
            )
    
    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        data = {}
        
        # Generic price patterns
        price_patterns = [
            r'\$(\d{1,3}(?:,\d{3})+)',
            r'£(\d{1,3}(?:,\d{3})+)',
            r'€(\d{1,3}(?:,\d{3})+)',
        ]
        for pattern in price_patterns:
            if re.search(pattern, html):
                data["price"] = self.extract_number(re.search(pattern, html).group())
                if "£" in pattern:
                    data["currency"] = "GBP"
                elif "€" in pattern:
                    data["currency"] = "EUR"
                break
        
        # Beds
        beds_patterns = [
            r'(\d+)\s*bed',
            r'(\d+)\s*bedroom',
        ]
        for pattern in beds_patterns:
            if re.search(pattern, html, re.I):
                data["bedrooms"] = int(re.search(pattern, html, re.I).group(1))
                break
        
        # Baths
        baths_patterns = [
            r'(\d+)\s*bath',
            r'(\d+)\s*bathroom',
        ]
        for pattern in baths_patterns:
            if re.search(pattern, html, re.I):
                data["bathrooms"] = int(re.search(pattern, html, re.I).group(1))
                break
        
        return data


class ScraperRegistry:
    """Registry of all scraper adapters"""
    
    def __init__(self):
        self.adapters: List[BaseAdapter] = [
            ZillowAdapter(),
            RealtorAdapter(),
            RedfinAdapter(),
            RightmoveAdapter(),
            BayutAdapter(),
            PropertyFinderAdapter(),
            GenericAdapter(),  # Fallback
        ]
    
    def get_adapter(self, url: str) -> BaseAdapter:
        """Get the appropriate adapter for a URL"""
        for adapter in self.adapters:
            if adapter.can_handle(url):
                return adapter
        return self.adapters[-1]  # Return generic as fallback
    
    def get_supported_sources(self) -> List[Dict[str, str]]:
        """Get list of supported sources"""
        return [
            {"name": a.name, "domains": ", ".join(a.supported_domains) if a.supported_domains else "All"}
            for a in self.adapters[:-1]  # Exclude generic
        ]


# Global registry instance
registry = ScraperRegistry()


async def scrape_property(url: str) -> Dict[str, Any]:
    """
    Main entry point for scraping a property URL.
    Returns normalized property data.
    """
    adapter = registry.get_adapter(url)
    
    try:
        property_data = await adapter.scrape(url)
        return {
            "success": True,
            "property": property_data.to_dict(),
            "source": adapter.name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "source": adapter.name
        }
