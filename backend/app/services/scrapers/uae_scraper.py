"""
UAE Property Listings Scraper
Fetches property listings from UAE real estate websites
"""
import asyncio
import re
import json
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.models import Property
from app.database import SessionLocal


class UAEScraper:
    """Base scraper for UAE real estate listings"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.rate_limit = 2.0
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers=self.headers,
                follow_redirects=True
            )
        return self.session
    
    async def _fetch(self, url: str) -> Optional[str]:
        try:
            client = await self._get_session()
            await asyncio.sleep(self.rate_limit)
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_price(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.replace(",", "").replace(" ", "")
        match = re.search(r"[\d.]+", text)
        if match:
            try:
                return float(match.group())
            except:
                pass
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        if not text:
            return None
        match = re.search(r"\d+", text)
        if match:
            return int(match.group())
        return None
    
    def _extract_area(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.replace(",", "")
        match = re.search(r"[\d.]+", text)
        if match:
            try:
                return float(match.group())
            except:
                pass
        return None
    
    async def scrape_listings(self, city: str = "dubai", limit: int = 50) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    def save_to_database(self, listings: List[Dict[str, Any]]) -> int:
        db = SessionLocal()
        saved = 0
        try:
            for item in listings:
                existing = db.query(Property).filter(
                    Property.source_url == item.get("source_url")
                ).first()
                
                if existing:
                    for key, value in item.items():
                        if value is not None and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    property = Property(
                        title=item.get("title"),
                        description=item.get("description"),
                        price=item.get("price"),
                        currency=item.get("currency", "AED"),
                        currency_symbol=item.get("currency_symbol", "د.إ"),
                        area=item.get("area"),
                        price_per_m2=item.get("price_per_m2"),
                        location=item.get("location"),
                        address=item.get("address"),
                        city=item.get("city"),
                        state=item.get("state", "Dubai"),
                        district=item.get("district"),
                        country=item.get("country", "UAE"),
                        region=item.get("region"),
                        property_type=item.get("property_type"),
                        bedrooms=item.get("bedrooms"),
                        bathrooms=item.get("bathrooms"),
                        year_built=item.get("year_built"),
                        parking=item.get("parking"),
                        latitude=item.get("latitude"),
                        longitude=item.get("longitude"),
                        image_url=item.get("image_url"),
                        source_url=item.get("source_url"),
                        source=item.get("source"),
                    )
                    db.add(property)
                
                saved += 1
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving to database: {e}")
        finally:
            db.close()
        
        return saved


class BayutScraper(UAEScraper):
    """Scraper for Bayut.com listings"""
    
    BASE_URL = "https://www.bayut.com"
    
    async def scrape_listings(self, city: str = "dubai", limit: int = 50) -> List[Dict[str, Any]]:
        listings = []
        
        city_path = f"/properties-for-sale/{city}/"
        page = 1
        collected = 0
        
        while collected < limit:
            url = f"{self.BASE_URL}{city_path}"
            if page > 1:
                url = f"{self.BASE_URL}{city_path}?page={page}"
            
            html = await self._fetch(url)
            if not html:
                break
            
            soup =Soup(html)
            cards = soup.find_all("article", {"class": lambda x: x and "PropertyCard" in x})
            
            if not cards:
                break
            
            for card in cards:
                if collected >= limit:
                    break
                
                try:
                    listing = self._parse_card(card, city)
                    if listing:
                        listings.append(listing)
                        collected += 1
                except Exception as e:
                    print(f"Error parsing card: {e}")
                    continue
            
            page += 1
            await asyncio.sleep(1)
        
        return listings
    
    def _parse_card(self, card: BeautifulSoup, city: str) -> Optional[Dict[str, Any]]:
        title_elem = card.find("h2") or card.find("a", {"class": lambda x: x and "title" in x})
        title = title_elem.get_text(strip=True) if title_elem else None
        
        price_elem = card.find("span", {"class": lambda x: x and "price" in x})
        price_text = price_elem.get_text(strip=True) if price_elem else None
        price = self._extract_price(price_text)
        
        location_elem = card.find("div", {"class": lambda x: x and "location" in x})
        location = location_elem.get_text(strip=True) if location_elem else None
        
        link_elem = card.find("a", href=True)
        source_url = f"{self.BASE_URL}{link_elem['href']}" if link_elem and link_elem.get("href") else None
        
        beds_elem = card.find("span", {"class": lambda x: x and "bed" in x})
        bedrooms = self._extract_number(beds_elem.get_text(strip=True) if beds_elem else None)
        
        baths_elem = card.find("span", {"class": lambda x: x and "bath" in x})
        bathrooms = self._extract_number(baths_elem.get_text(strip=True) if baths_elem else None)
        
        area_elem = card.find("span", {"class": lambda x: x and "area" in x})
        area = self._extract_area(area_elem.get_text(strip=True) if area_elem else None)
        
        img_elem = card.find("img")
        image_url = img_elem.get("src") if img_elem else None
        
        property_type = self._infer_property_type(title or location or "")
        
        return {
            "title": title,
            "description": location,
            "price": price,
            "currency": "AED",
            "currency_symbol": "د.إ",
            "area": area,
            "price_per_m2": round(price / area, 2) if price and area else None,
            "location": location,
            "city": city.title(),
            "country": "UAE",
            "property_type": property_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "image_url": image_url,
            "source_url": source_url,
            "source": "bayut",
        }
    
    def _infer_property_type(self, text: str) -> str:
        text = text.lower()
        if "villa" in text:
            return "villa"
        elif "apartment" in text or "flat" in text:
            return "apartment"
        elif "townhouse" in text:
            return "townhouse"
        elif "penthouse" in text:
            return "penthouse"
        elif "studio" in text:
            return "studio"
        elif "plot" in text or "land" in text:
            return "plot"
        return "apartment"


class PropertyFinderScraper(UAEScraper):
    """Scraper for PropertyFinder.ae listings"""
    
    BASE_URL = "https://www.propertyfinder.ae"
    
    async def scrape_listings(self, city: str = "dubai", limit: int = 50) -> List[Dict[str, Any]]:
        listings = []
        
        city_path = f"/en/search/?city={city}"
        page = 1
        collected = 0
        
        while collected < limit:
            url = f"{self.BASE_URL}{city_path}"
            if page > 1:
                url = f"{self.BASE_URL}{city_path}&page={page}"
            
            html = await self._fetch(url)
            if not html:
                break
            
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("div", {"class": lambda x: x and "property-card" in x})
            
            if not cards:
                break
            
            for card in cards:
                if collected >= limit:
                    break
                
                try:
                    listing = self._parse_card(card, city)
                    if listing:
                        listings.append(listing)
                        collected += 1
                except Exception as e:
                    print(f"Error parsing card: {e}")
                    continue
            
            page += 1
            await asyncio.sleep(1)
        
        return listings
    
    def _parse_card(self, card: BeautifulSoup, city: str) -> Optional[Dict[str, Any]]:
        title_elem = card.find("h2") or card.find("a", {"class": lambda x: x and "title" in x})
        title = title_elem.get_text(strip=True) if title_elem else None
        
        price_elem = card.find("span", {"class": lambda x: x and "price" in x})
        price_text = price_elem.get_text(strip=True) if price_elem else None
        price = self._extract_price(price_text)
        
        location_elem = card.find("div", {"class": lambda x: x and "location" in x})
        location = location_elem.get_text(strip=True) if location_elem else None
        
        link_elem = card.find("a", href=True)
        source_url = f"{self.BASE_URL}{link_elem['href']}" if link_elem and link_elem.get("href") else None
        
        beds_elem = card.find("li", {"class": lambda x: x and "bed" in x})
        bedrooms = self._extract_number(beds_elem.get_text(strip=True) if beds_elem else None)
        
        baths_elem = card.find("li", {"class": lambda x: x and "bath" in x})
        bathrooms = self._extract_number(baths_elem.get_text(strip=True) if baths_elem else None)
        
        area_elem = card.find("li", {"class": lambda x: x and "sqft" in x or "sqm" in x})
        area = self._extract_area(area_elem.get_text(strip=True) if area_elem else None)
        
        img_elem = card.find("img")
        image_url = img_elem.get("src") or img_elem.get("data-src") if img_elem else None
        
        property_type = self._infer_property_type(title or location or "")
        
        return {
            "title": title,
            "description": location,
            "price": price,
            "currency": "AED",
            "currency_symbol": "د.إ",
            "area": area,
            "price_per_m2": round(price / area, 2) if price and area else None,
            "location": location,
            "city": city.title(),
            "country": "UAE",
            "property_type": property_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "image_url": image_url,
            "source_url": source_url,
            "source": "propertyfinder",
        }
    
    def _infer_property_type(self, text: str) -> str:
        text = text.lower()
        if "villa" in text:
            return "villa"
        elif "apartment" in text or "flat" in text:
            return "apartment"
        elif "townhouse" in text:
            return "townhouse"
        elif "penthouse" in text:
            return "penthouse"
        elif "studio" in text:
            return "studio"
        elif "plot" in text or "land" in text:
            return "plot"
        return "apartment"


class DubizzleScraper(UAEScraper):
    """Scraper for Dubizzle.com property listings"""
    
    BASE_URL = "https://www.dubizzle.com"
    
    async def scrape_listings(self, city: str = "dubai", limit: int = 50) -> List[Dict[str, Any]]:
        listings = []
        
        city_map = {
            "dubai": "dubai",
            "abu dhabi": "abu-dhabi",
            "sharjah": "sharjah",
            "ajman": "ajman",
            "ras al khaimah": "ras-al-khaimah",
            "fujairah": "fujairah",
            "umm al quwain": "umm-al-quwain",
        }
        
        city_slug = city_map.get(city.lower(), "dubai")
        category = "properties-for-sale"
        url = f"{self.BASE_URL}/uae/{city_slug}/{category}/"
        
        page = 1
        collected = 0
        
        while collected < limit:
            page_url = url if page == 1 else f"{url}?page={page}"
            
            html = await self._fetch(page_url)
            if not html:
                break
            
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("li", {"class": lambda x: x and "Listing" in x})
            
            if not cards:
                cards = soup.find_all("div", {"class": lambda x: x and "listing" in x})
            
            if not cards:
                break
            
            for card in cards:
                if collected >= limit:
                    break
                
                try:
                    listing = self._parse_card(card, city)
                    if listing:
                        listings.append(listing)
                        collected += 1
                except Exception as e:
                    print(f"Error parsing card: {e}")
                    continue
            
            page += 1
            await asyncio.sleep(1)
        
        return listings
    
    def _parse_card(self, card: BeautifulSoup, city: str) -> Optional[Dict[str, Any]]:
        title_elem = card.find("a") or card.find("h2")
        title = title_elem.get_text(strip=True) if title_elem else None
        
        price_elem = card.find("span", {"class": lambda x: x and "price" in x})
        price_text = price_elem.get_text(strip=True) if price_elem else None
        price = self._extract_price(price_text)
        
        location_elem = card.find("span", {"class": lambda x: x and "location" in x})
        location = location_elem.get_text(strip=True) if location_elem else None
        
        link_elem = card.find("a", href=True)
        source_url = link_elem.get("href") if link_elem else None
        if source_url and not source_url.startswith("http"):
            source_url = f"{self.BASE_URL}{source_url}"
        
        beds_elem = card.find("span", {"class": lambda x: x and "bed" in x})
        bedrooms = self._extract_number(beds_elem.get_text(strip=True) if beds_elem else None)
        
        baths_elem = card.find("span", {"class": lambda x: x and "bath" in x})
        bathrooms = self._extract_number(baths_elem.get_text(strip=True) if baths_elem else None)
        
        area_elem = card.find("span", {"class": lambda x: x and "sqft" in x or "sqm" in x or "area" in x})
        area = self._extract_area(area_elem.get_text(strip=True) if area_elem else None)
        
        img_elem = card.find("img")
        image_url = img_elem.get("src") or img_elem.get("data-src") if img_elem else None
        
        property_type = self._infer_property_type(title or location or "")
        
        return {
            "title": title,
            "description": location,
            "price": price,
            "currency": "AED",
            "currency_symbol": "د.إ",
            "area": area,
            "price_per_m2": round(price / area, 2) if price and area else None,
            "location": location,
            "city": city.title(),
            "country": "UAE",
            "property_type": property_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "image_url": image_url,
            "source_url": source_url,
            "source": "dubizzle",
        }
    
    def _infer_property_type(self, text: str) -> str:
        text = text.lower()
        if "villa" in text:
            return "villa"
        elif "apartment" in text or "flat" in text:
            return "apartment"
        elif "townhouse" in text:
            return "townhouse"
        elif "penthouse" in text:
            return "penthouse"
        elif "studio" in text:
            return "studio"
        elif "plot" in text or "land" in text:
            return "plot"
        elif "building" in text:
            return "commercial"
        return "apartment"


async def scrape_all_sources(cities: List[str] = None, limit_per_source: int = 50) -> Dict[str, int]:
    """
    Run all UAE scrapers and save to database
    """
    if cities is None:
        cities = ["dubai", "abu dhabi", "sharjah"]
    
    scrapers = [
        BayutScraper(),
        PropertyFinderScraper(),
        DubizzleScraper(),
    ]
    
    results = {}
    
    for scraper in scrapers:
        source_name = scraper.__class__.__name__.replace("Scraper", "").lower()
        total_saved = 0
        
        for city in cities:
            print(f"Scraping {source_name} for {city}...")
            try:
                listings = await scraper.scrape_listings(city, limit_per_source)
                if listings:
                    saved = scraper.save_to_database(listings)
                    total_saved += saved
                    print(f"  Saved {saved} listings from {city}")
            except Exception as e:
                print(f"  Error scraping {city}: {e}")
        
        results[source_name] = total_saved
    
    return results


if __name__ == "__main__":
    asyncio.run(scrape_all_sources())
