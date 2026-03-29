"""
Unified Property Analyzer
Combines UAE market data with global property analysis.
Output format: roi_percent, deal_score, risk_level, tags, recommendation
"""

import asyncio
import re
from typing import Optional, Dict, Any
from app.services.real_estate_api.uae_market import UAEMarketService
from app.services.scrapers.adapters_usa import us_scraper


uae_service = UAEMarketService()


class PropertyAnalyzer:
    """
    Unified property analyzer for UAE and global properties.
    Generates comprehensive analysis with ROI, deal score, and recommendations.
    """
    
    # Property type mappings
    PROPERTY_TYPE_MAP = {
        "villa": "Villa",
        "townhouse": "Townhouse",
        "apartment": "Apartment",
        "penthouse": "Penthouse",
        "studio": "Studio",
        "single_family": "Villa",
        "condo": "Apartment",
    }
    
    def __init__(self):
        self.uae = uae_service
    
    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analyze property from URL.
        Supports: Bayut, PropertyFinder, Zillow, Redfin, Realtor
        """
        # Detect URL type and scrape
        property_data = await self._scrape_url(url)
        
        if not property_data:
            return {
                "success": False,
                "error": "Could not scrape property data",
                "url": url,
            }
        
        # Detect market and analyze
        if self._is_uae_url(url):
            return await self._analyze_uae_property(property_data, url)
        else:
            return await self._analyze_global_property(property_data, url)
    
    def _is_uae_url(self, url: str) -> bool:
        """Check if URL is UAE property site."""
        url_lower = url.lower()
        return any(site in url_lower for site in ["bayut", "propertyfinder", "dubizzle"])
    
    async def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape property data from URL."""
        url_lower = url.lower()
        
        # UAE sites
        if "bayut" in url_lower:
            return await self._scrape_bayut(url)
        elif "propertyfinder" in url_lower:
            return await self._scrape_propertyfinder(url)
        
        # US sites
        if any(site in url_lower for site in ["zillow", "redfin", "realtor"]):
            return await us_scraper.scrape(url)
        
        # Generic fallback
        return await self._generic_scrape(url)
    
    async def _scrape_bayut(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape from Bayut.com"""
        try:
            from app.services.scrapers import scrape_url
            result = await scrape_url(url)
            if result:
                return {
                    "source": "Bayut",
                    "url": url,
                    "title": result.get("property", {}).get("title"),
                    "price": result.get("property", {}).get("price"),
                    "currency": result.get("property", {}).get("currency", "AED"),
                    "area_sqft": result.get("property", {}).get("area"),
                    "bedrooms": result.get("property", {}).get("bedrooms"),
                    "bathrooms": result.get("property", {}).get("bathrooms"),
                    "property_type": result.get("property", {}).get("property_type"),
                    "city": result.get("property", {}).get("city"),
                    "location": result.get("property", {}).get("location"),
                }
        except Exception as e:
            print(f"Bayut scrape error: {e}")
        return None
    
    async def _scrape_propertyfinder(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape from PropertyFinder.ae"""
        try:
            from app.services.scrapers import scrape_url
            result = await scrape_url(url)
            if result:
                return {
                    "source": "PropertyFinder",
                    "url": url,
                    "title": result.get("property", {}).get("title"),
                    "price": result.get("property", {}).get("price"),
                    "currency": result.get("property", {}).get("currency", "AED"),
                    "area_sqft": result.get("property", {}).get("area"),
                    "bedrooms": result.get("property", {}).get("bedrooms"),
                    "bathrooms": result.get("property", {}).get("bathrooms"),
                    "property_type": result.get("property", {}).get("property_type"),
                    "city": result.get("property", {}).get("city"),
                }
        except Exception as e:
            print(f"PropertyFinder scrape error: {e}")
        return None
    
    async def _generic_scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """Generic URL scraping fallback."""
        return {
            "source": "Unknown",
            "url": url,
            "title": "Property",
            "price": None,
            "currency": "USD",
        }
    
    async def _analyze_uae_property(
        self, 
        data: Dict[str, Any],
        url: str
    ) -> Dict[str, Any]:
        """Analyze UAE property with local market data."""
        # Detect area from location
        area_name = self._extract_uae_area(data.get("location") or data.get("city", ""))
        
        # Get market data for area
        market_data = self.uae.get_area_data(area_name)
        
        if not market_data:
            # Use default Dubai data
            market_data = self.uae.get_area_data("jvc")
        
        # Calculate property metrics
        price = data.get("price") or market_data.get("medianPrice", 1000000)
        area = data.get("area_sqft") or 1000
        price_per_sqft = price / area if area > 0 else market_data.get("avgPricePerSqFt", 1000)
        
        # Calculate ROI
        monthly_rent = market_data.get("avgRent", 6000)
        annual_rent = monthly_rent * 12
        annual_expenses = price * 0.04  # ~4% for service charges,物业费
        net_income = annual_rent - annual_expenses
        roi_percent = (net_income / price) * 100 if price > 0 else 0
        
        # Compare to market
        avg_price_sqft = market_data.get("avgPricePerSqFt", 1000)
        price_diff_pct = ((price_per_sqft - avg_price_sqft) / avg_price_sqft) * 100
        
        # Calculate deal score
        deal_score = self._calculate_deal_score(
            roi=roi_percent,
            price_vs_market=price_diff_pct,
            market_data=market_data,
            area=area,
            property_type=data.get("property_type"),
        )
        
        # Generate tags
        tags = self._generate_tags(
            roi=roi_percent,
            price_vs_market=price_diff_pct,
            risk_level=market_data.get("riskLevel", "Medium"),
            deal_score=deal_score,
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            deal_score=deal_score,
            roi=roi_percent,
            price_diff_pct=price_diff_pct,
            risk_level=market_data.get("riskLevel", "Medium"),
        )
        
        return {
            "success": True,
            "url": url,
            "source": data.get("source", "Bayut/PropertyFinder"),
            "property": {
                "title": data.get("title"),
                "price": price,
                "currency": data.get("currency", "AED"),
                "area_sqft": area,
                "bedrooms": data.get("bedrooms"),
                "bathrooms": data.get("bathrooms"),
                "property_type": data.get("property_type"),
                "location": data.get("location") or data.get("city"),
                "area": area_name,
            },
            "analysis": {
                "roi_percent": round(roi_percent, 1),
                "deal_score": deal_score,
                "risk_level": market_data.get("riskLevel", "Medium"),
                "price_vs_market": f"{abs(price_diff_pct):.1f}% {'above' if price_diff_pct > 0 else 'below'} area average",
                "avg_area_price_sqft": avg_price_sqft,
                "monthly_rent_estimate": monthly_rent,
                "annual_rent_estimate": annual_rent,
                "annual_expenses_estimate": annual_expenses,
                "net_yield": round(roi_percent, 1),
                "tags": tags,
                "recommendation": recommendation,
                "data_source": f"{market_data.get('dataSource')} + {data.get('source')} listings",
            },
            "market_context": {
                "area": area_name,
                "area_arabic": market_data.get("nameAr"),
                "area_avg_yield": market_data.get("avgRentYield"),
                "area_avg_price_sqft": avg_price_sqft,
                "area_transactions_2024": market_data.get("transactions2024"),
                "price_trend": market_data.get("priceTrend"),
            },
        }
    
    async def _analyze_global_property(
        self,
        data: Dict[str, Any],
        url: str
    ) -> Dict[str, Any]:
        """Analyze non-UAE property with global market data."""
        price = data.get("price") or 500000
        area = data.get("area_sqft") or 2000
        price_per_sqft = price / area if area > 0 else 250
        
        # Estimate rent (use 1% rule of thumb)
        monthly_rent = price * 0.005
        annual_rent = monthly_rent * 12
        annual_expenses = price * 0.015  # ~1.5% for taxes, insurance, maintenance
        net_income = annual_rent - annual_expenses
        roi_percent = (net_income / price) * 100 if price > 0 else 0
        
        # Market comparison (use USA average)
        usa_avg_price_sqft = 250
        price_diff_pct = ((price_per_sqft - usa_avg_price_sqft) / usa_avg_price_sqft) * 100
        
        # Calculate deal score
        deal_score = self._calculate_deal_score_global(
            roi=roi_percent,
            price_vs_market=price_diff_pct,
            area=area,
            year_built=data.get("year_built"),
        )
        
        # Generate tags
        tags = self._generate_tags(
            roi=roi_percent,
            price_vs_market=price_diff_pct,
            risk_level="Medium" if price > 1000000 else "Low",
            deal_score=deal_score,
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            deal_score=deal_score,
            roi=roi_percent,
            price_diff_pct=price_diff_pct,
            risk_level="Medium",
        )
        
        return {
            "success": True,
            "url": url,
            "source": data.get("source", "Unknown"),
            "property": {
                "title": data.get("title"),
                "price": price,
                "currency": data.get("currency", "USD"),
                "area_sqft": area,
                "bedrooms": data.get("bedrooms"),
                "bathrooms": data.get("bathrooms"),
                "property_type": data.get("property_type"),
                "year_built": data.get("year_built"),
                "city": data.get("city"),
                "state": data.get("state"),
            },
            "analysis": {
                "roi_percent": round(roi_percent, 1),
                "deal_score": deal_score,
                "risk_level": "Medium" if price > 1000000 else "Low",
                "price_vs_market": f"{abs(price_diff_pct):.1f}% {'above' if price_diff_pct > 0 else 'below'} US average",
                "avg_area_price_sqft": usa_avg_price_sqft,
                "monthly_rent_estimate": round(monthly_rent, 0),
                "annual_rent_estimate": round(annual_rent, 0),
                "annual_expenses_estimate": round(annual_expenses, 0),
                "net_yield": round(roi_percent, 1),
                "tags": tags,
                "recommendation": recommendation,
                "data_source": f"{data.get('source')} listings + market averages",
            },
        }
    
    def _extract_uae_area(self, location: str) -> str:
        """Extract area name from location string."""
        if not location:
            return "jvc"
        
        location_lower = location.lower()
        
        area_mappings = {
            "marina": "dubai_marina",
            "downtown": "downtown_dubai",
            "business bay": "business_bay",
            "palm": "palm_jumeirah",
            "jvc": "jvc",
            "jumeirah village": "jvc",
            "international city": "international_city",
            "dubai hills": "dubai_hills",
            "barsha": "al_barsha",
            "jbr": "jbr",
            "creek": "creek_harbour",
            "silicon": "dubai_silicon_oasis",
            "motor": "motor_city",
            "greens": "greens",
            "sports": "sports_city",
            "discovery": "discovery_gardens",
            "lakes": "jumeirah_lake_towers",
            "land": "dubai_land",
            "mudon": "mudon",
            "arabian": "arabian_ranches",
            "emirates": "emirates_living",
            "victory": "victory_heights",
            "springs": "the_springs",
            "meadows": "meadows",
        }
        
        for key, area in area_mappings.items():
            if key in location_lower:
                return area
        
        return "jvc"  # Default
    
    def _calculate_deal_score(
        self,
        roi: float,
        price_vs_market: float,
        market_data: Dict,
        area: float,
        property_type: str,
    ) -> int:
        """Calculate deal score (0-100) for UAE properties."""
        score = 50  # Base
        
        # ROI contribution (up to +25)
        if roi >= 8:
            score += 25
        elif roi >= 7:
            score += 20
        elif roi >= 6:
            score += 15
        elif roi >= 5:
            score += 10
        else:
            score += 5
        
        # Price vs market (up to +25)
        if price_vs_market <= -15:
            score += 25
        elif price_vs_market <= -10:
            score += 20
        elif price_vs_market <= -5:
            score += 15
        elif price_vs_market <= 0:
            score += 10
        else:
            score += 0
        
        # Risk level (up to +15)
        risk = market_data.get("riskLevel", "Medium")
        if risk == "Low":
            score += 15
        elif risk == "Medium":
            score += 10
        else:
            score += 5
        
        # Price trend (up to +15)
        trend = market_data.get("priceTrend", "stable")
        if trend == "rising":
            score += 15
        elif trend == "stable":
            score += 10
        else:
            score += 5
        
        # Transaction volume (up to +10)
        transactions = market_data.get("transactions2024", 0)
        if transactions > 3000:
            score += 10
        elif transactions > 1000:
            score += 7
        else:
            score += 3
        
        return min(max(score, 0), 100)
    
    def _calculate_deal_score_global(
        self,
        roi: float,
        price_vs_market: float,
        area: float,
        year_built: int,
    ) -> int:
        """Calculate deal score for global properties."""
        score = 50
        
        # ROI (up to +30)
        if roi >= 10:
            score += 30
        elif roi >= 8:
            score += 25
        elif roi >= 6:
            score += 15
        elif roi >= 4:
            score += 10
        
        # Price vs market (up to +30)
        if price_vs_market <= -20:
            score += 30
        elif price_vs_market <= -10:
            score += 20
        elif price_vs_market <= 0:
            score += 10
        
        # Age bonus (up to +10)
        if year_built and year_built >= 2020:
            score += 10
        elif year_built and year_built >= 2010:
            score += 5
        
        return min(max(score, 0), 100)
    
    def _generate_tags(
        self,
        roi: float,
        price_vs_market: float,
        risk_level: str,
        deal_score: int,
    ) -> list:
        """Generate property tags."""
        tags = []
        
        # ROI tags
        if roi >= 8:
            tags.append("High ROI")
        elif roi >= 6:
            tags.append("Good ROI")
        elif roi >= 4:
            tags.append("Fair ROI")
        
        # Price tags
        if price_vs_market <= -15:
            tags.append("Undervalued")
        elif price_vs_market <= -5:
            tags.append("Below Market")
        elif price_vs_market >= 15:
            tags.append("Premium Price")
        
        # Deal score tags
        if deal_score >= 80:
            tags.append("Strong Opportunity")
        elif deal_score >= 60:
            tags.append("Decent Deal")
        
        # Risk tags
        if risk_level == "Low":
            tags.append("Low Risk")
        elif risk_level == "High":
            tags.append("High Risk")
        
        # Special tags
        if roi >= 8 and price_vs_market <= -10:
            tags.append("Best Pick")
        
        return tags[:5]  # Max 5 tags
    
    def _generate_recommendation(
        self,
        deal_score: int,
        roi: float,
        price_diff_pct: float,
        risk_level: str,
    ) -> str:
        """Generate investment recommendation."""
        if deal_score >= 80:
            return "Excellent opportunity — high rental yield with competitive pricing. Strong recommendation to buy."
        elif deal_score >= 65:
            return "Good opportunity — solid rental yield with reasonable pricing. Consider purchasing."
        elif deal_score >= 50:
            return "Fair deal — moderate returns and pricing. Watch for price negotiations."
        elif deal_score >= 35:
            return "Below average deal — consider negotiating lower price or waiting for better opportunities."
        else:
            return "Not recommended — pricing above market or yields below acceptable thresholds."


analyzer = PropertyAnalyzer()
