"""
RentCast API Integration
Fetches real property data for analysis
"""
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings


class RentCastAPI:
    """Client for RentCast API"""
    
    BASE_URL = "https://api.rentcast.io/v1"
    
    def __init__(self):
        self.api_key = settings.RENTCAST_API_KEY
        self.timeout = 30.0
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_property_details(self, address: str, city: str = None, state: str = None) -> Optional[Dict]:
        """Get property details by address"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"address": address}
                if city:
                    params["city"] = city
                if state:
                    params["state"] = state
                
                response = await client.get(
                    f"{self.BASE_URL}/property",
                    headers=self._get_headers(),
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"RentCast API error: {e}")
            return None
    
    async def get_market_rent(self, city: str, state: str, bedrooms: int = None) -> Optional[Dict]:
        """Get market rent estimates for a location"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"city": city, "state": state}
                if bedrooms is not None:
                    params["bedrooms"] = bedrooms
                
                response = await client.get(
                    f"{self.BASE_URL}/marketRent",
                    headers=self._get_headers(),
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"RentCast API error: {e}")
            return None
    
    async def get_comps(self, address: str, max_radius: int = 1) -> Optional[List[Dict]]:
        """Get comparable properties"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/comps",
                    headers=self._get_headers(),
                    params={"address": address, "maxRadius": max_radius, "limit": 5}
                )
                
                if response.status_code == 200:
                    return response.json().get("comparables", [])
                return None
        except Exception as e:
            print(f"RentCast API error: {e}")
            return None
    
    async def get_avm(self, address: str) -> Optional[Dict]:
        """Get Automated Valuation Model (AVM)"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/avm",
                    headers=self._get_headers(),
                    params={"address": address}
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"RentCast API error: {e}")
            return None


rentcast = RentCastAPI()


async def analyze_property_with_rentcast(address: str, city: str = None, state: str = None) -> Dict[str, Any]:
    """
    Full property analysis using RentCast API
    """
    result = {
        "source": "rentcast",
        "address": address,
        "found": False,
        "price": None,
        "area": None,
        "bedrooms": None,
        "bathrooms": None,
        "year_built": None,
        "lot_size": None,
        "rent_estimate": None,
        "avm_value": None,
        "avm_low": None,
        "avm_high": None,
        "comparables": [],
        "market_rent": None
    }
    
    if not settings.RENTCAST_API_KEY:
        result["error"] = "RentCast API key not configured"
        return result
    
    property_data = await rentcast.get_property_details(address, city, state)
    
    if property_data:
        result["found"] = True
        result["price"] = property_data.get("lastSalePrice") or property_data.get("estimatedValue")
        result["area"] = property_data.get("squareFootage")
        result["bedrooms"] = property_data.get("bedrooms")
        result["bathrooms"] = property_data.get("bathrooms")
        result["year_built"] = property_data.get("yearBuilt")
        result["lot_size"] = property_data.get("lotSize")
        result["latitude"] = property_data.get("latitude")
        result["longitude"] = property_data.get("longitude")
        
        city = city or property_data.get("city")
        state = state or property_data.get("state")
        
        if city and state:
            market_rent = await rentcast.get_market_rent(city, state, result["bedrooms"])
            if market_rent:
                result["market_rent"] = market_rent.get("marketRent") or market_rent.get("rent")
                result["rent_estimate"] = result["market_rent"]
        
        avm_data = await rentcast.get_avm(address)
        if avm_data:
            result["avm_value"] = avm_data.get("avm")
            result["avm_low"] = avm_data.get("avmLow")
            result["avm_high"] = avm_data.get("avmHigh")
        
        comps = await rentcast.get_comps(address)
        if comps:
            result["comparables"] = comps[:5]
    
    return result


def calculate_deal_score(price: float, area: float, rent_monthly: float = None, avm_value: float = None) -> Dict[str, Any]:
    """
    Calculate deal score based on property data
    """
    if not price or not area:
        return {"score": 50, "label": "Average", "roi": 0, "price_per_sqm": 0}
    
    price_per_sqm = price / area
    
    MARKET_AVERAGES = {
        "usa": {"avg_price_sqm": 5000, "avg_rent_sqm": 35, "growth": 4.5},
        "uk": {"avg_price_sqm": 8000, "avg_rent_sqm": 40, "growth": 4.0},
        "uae": {"avg_price_sqm": 4000, "avg_rent_sqm": 75, "growth": 8.0},
        "canada": {"avg_price_sqm": 6000, "avg_rent_sqm": 38, "growth": 5.0},
        "australia": {"avg_price_sqm": 7000, "avg_rent_sqm": 40, "growth": 5.5},
        "default": {"avg_price_sqm": 5000, "avg_rent_sqm": 35, "growth": 4.5}
    }
    
    market = MARKET_AVERAGES["default"]
    market_avg = market["avg_price_sqm"]
    market_rent_sqm = market["avg_rent_sqm"]
    
    price_diff_pct = ((market_avg - price_per_sqm) / market_avg) * 100
    
    if rent_monthly:
        annual_rent = rent_monthly * 12
        roi = (annual_rent / price) * 100 if price > 0 else 0
    else:
        estimated_rent = area * market_rent_sqm
        annual_rent = estimated_rent * 12
        roi = (annual_rent / price) * 100 if price > 0 else 0
    
    score = 50
    if price_diff_pct > 0:
        score += min(30, price_diff_pct * 2)
    else:
        score += max(-20, price_diff_pct * 1.5)
    
    score += min(15, market["growth"] * 1.5)
    
    if 4 <= roi <= 10:
        score += min(15, roi * 1.2)
    elif roi > 10:
        score += 12
    
    if avm_value and price:
        price_vs_avm = ((avm_value - price) / avm_value) * 100
        if price_vs_avm > 0:
            score += min(10, price_vs_avm)
    
    score = min(100, max(0, int(score)))
    
    label = "Great Deal" if score >= 75 else "Average" if score >= 50 else "Overpriced"
    
    return {
        "score": score,
        "label": label,
        "roi": round(roi, 1),
        "price_per_sqm": round(price_per_sqm, 2),
        "price_diff_percent": round(price_diff_pct, 1),
        "market_avg": market_avg
    }
