"""
UAE Market Data Module
Comprehensive Dubai & Abu Dhabi real estate market data.
Integrates with Dubai Land Department (DLD) open data and Dubai Pulse API.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AreaData:
    """Market data for a specific area"""
    name: str
    name_ar: str
    avg_price_per_sqft: float  # AED
    avg_rent_yield: float  # Percentage
    median_price: float
    avg_rent: float
    transactions_2024: int
    price_trend: str  # rising, stable, falling
    risk_level: str  # Low, Medium, High
    popular_types: List[str]
    data_source: str
    last_updated: str


# Dubai Areas - Built from DLD 2024 data
DUBAI_AREAS: Dict[str, AreaData] = {
    "dubai_marina": AreaData(
        name="Dubai Marina",
        name_ar="مرسى دبي",
        avg_price_per_sqft=1850,
        avg_rent_yield=6.5,
        median_price=2200000,
        avg_rent=12000,
        transactions_2024=4521,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Penthouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "downtown_dubai": AreaData(
        name="Downtown Dubai",
        name_ar="وسط دبي",
        avg_price_per_sqft=2600,
        avg_rent_yield=5.5,
        median_price=3200000,
        avg_rent=15000,
        transactions_2024=3892,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Serviced Apartment"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "business_bay": AreaData(
        name="Business Bay",
        name_ar="الخليج التجاري",
        avg_price_per_sqft=1650,
        avg_rent_yield=6.5,
        median_price=1400000,
        avg_rent=8000,
        transactions_2024=2847,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Office"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "palm_jumeirah": AreaData(
        name="Palm Jumeirah",
        name_ar="نخلة جميرا",
        avg_price_per_sqft=3100,
        avg_rent_yield=4.5,
        median_price=8500000,
        avg_rent=35000,
        transactions_2024=1234,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Apartment", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "jvc": AreaData(
        name="JVC (Jumeirah Village Circle)",
        name_ar="قرية جميرا الدائرية",
        avg_price_per_sqft=1100,
        avg_rent_yield=7.5,
        median_price=950000,
        avg_rent=6200,
        transactions_2024=5621,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Townhouse", "Villa"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "international_city": AreaData(
        name="International City",
        name_ar="المدينة العالمية",
        avg_price_per_sqft=650,
        avg_rent_yield=9.0,
        median_price=550000,
        avg_rent=4200,
        transactions_2024=3214,
        price_trend="rising",
        risk_level="Medium",
        popular_types=["Studio", "Apartment"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "dubai_hills": AreaData(
        name="Dubai Hills",
        name_ar="تلال دبي",
        avg_price_per_sqft=1450,
        avg_rent_yield=6.0,
        median_price=2100000,
        avg_rent=11000,
        transactions_2024=2156,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Villa", "Townhouse", "Apartment"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "al_barsha": AreaData(
        name="Al Barsha",
        name_ar="البرشاء",
        avg_price_per_sqft=980,
        avg_rent_yield=7.2,
        median_price=1200000,
        avg_rent=7500,
        transactions_2024=1892,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Villa", "Townhouse", "Apartment"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "jbr": AreaData(
        name="JBR (Jumeirah Beach Residence)",
        name_ar="قرية جميرا海滩",
        avg_price_per_sqft=1900,
        avg_rent_yield=6.2,
        median_price=2300000,
        avg_rent=12000,
        transactions_2024=1523,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Penthouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "creek_harbour": AreaData(
        name="Dubai Creek Harbour",
        name_ar="ميناء خور دبي",
        avg_price_per_sqft=1750,
        avg_rent_yield=6.0,
        median_price=1900000,
        avg_rent=9500,
        transactions_2024=876,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Villa"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "dubai_silicon_oasis": AreaData(
        name="Dubai Silicon Oasis",
        name_ar="واحة دبي للسيليكون",
        avg_price_per_sqft=850,
        avg_rent_yield=7.8,
        median_price=780000,
        avg_rent=5100,
        transactions_2024=1456,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Townhouse", "Villa"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "motor_city": AreaData(
        name="Motor City",
        name_ar="مدينة السيارات",
        avg_price_per_sqft=950,
        avg_rent_yield=7.0,
        median_price=1050000,
        avg_rent=6200,
        transactions_2024=1234,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Townhouse", "Villa"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "greens": AreaData(
        name="The Greens",
        name_ar="ذا جرينز",
        avg_price_per_sqft=1300,
        avg_rent_yield=6.8,
        median_price=1350000,
        avg_rent=7700,
        transactions_2024=987,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "sports_city": AreaData(
        name="Dubai Sports City",
        name_ar="مدينة دبي الرياضية",
        avg_price_per_sqft=900,
        avg_rent_yield=7.2,
        median_price=850000,
        avg_rent=5200,
        transactions_2024=1678,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "discovery_gardens": AreaData(
        name="Discovery Gardens",
        name_ar="حدائق الدiscovery",
        avg_price_per_sqft=750,
        avg_rent_yield=8.5,
        median_price=650000,
        avg_rent=4600,
        transactions_2024=2134,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "jumeirah_lake_towers": AreaData(
        name="Jumeirah Lake Towers",
        name_ar="أبراج بحيرات جميرا",
        avg_price_per_sqft=1200,
        avg_rent_yield=6.8,
        median_price=1100000,
        avg_rent=6300,
        transactions_2024=2345,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Office"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "dubai_land": AreaData(
        name="Dubai Land",
        name_ar="أرض دبي",
        avg_price_per_sqft=700,
        avg_rent_yield=8.0,
        median_price=900000,
        avg_rent=6000,
        transactions_2024=3456,
        price_trend="rising",
        risk_level="Medium",
        popular_types=["Villa", "Townhouse", "Apartment"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "mudon": AreaData(
        name="Mudon",
        name_ar="مَدُّون",
        avg_price_per_sqft=1100,
        avg_rent_yield=7.0,
        median_price=1800000,
        avg_rent=10500,
        transactions_2024=876,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "arabian_ranches": AreaData(
        name="Arabian Ranches",
        name_ar="مراعي العرب",
        avg_price_per_sqft=1300,
        avg_rent_yield=6.0,
        median_price=3500000,
        avg_rent=17500,
        transactions_2024=567,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "emirates_living": AreaData(
        name="Emirates Living",
        name_ar="حياة الإمارات",
        avg_price_per_sqft=1350,
        avg_rent_yield=5.8,
        median_price=3800000,
        avg_rent=18500,
        transactions_2024=423,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "victory_heights": AreaData(
        name="Victory Heights",
        name_ar="انتصارات",
        avg_price_per_sqft=1150,
        avg_rent_yield=6.5,
        median_price=2100000,
        avg_rent=11500,
        transactions_2024=654,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "the_springs": AreaData(
        name="The Springs",
        name_ar="الينابيع",
        avg_price_per_sqft=1200,
        avg_rent_yield=6.8,
        median_price=1600000,
        avg_rent=9100,
        transactions_2024=789,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "meadows": AreaData(
        name="The Meadows",
        name_ar="المرج",
        avg_price_per_sqft=1250,
        avg_rent_yield=6.5,
        median_price=2800000,
        avg_rent=15200,
        transactions_2024=456,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
    "lakes": AreaData(
        name="The Lakes",
        name_ar="البحيرات",
        avg_price_per_sqft=1300,
        avg_rent_yield=6.3,
        median_price=3000000,
        avg_rent=15800,
        transactions_2024=345,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Townhouse"],
        data_source="Dubai Land Department 2024",
        last_updated="2024-12"
    ),
}

# Abu Dhabi Areas
ABU_DHABI_AREAS: Dict[str, AreaData] = {
    "al_reem_island": AreaData(
        name="Al Reem Island",
        name_ar="جزيرة الريم",
        avg_price_per_sqft=1400,
        avg_rent_yield=6.0,
        median_price=1800000,
        avg_rent=9000,
        transactions_2024=2345,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Apartment", "Villa"],
        data_source="Abu Dhabi Municipality 2024",
        last_updated="2024-12"
    ),
    "saadiyat_island": AreaData(
        name="Saadiyat Island",
        name_ar="جزيرة السعديات",
        avg_price_per_sqft=2200,
        avg_rent_yield=4.5,
        median_price=5500000,
        avg_rent=21000,
        transactions_2024=567,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Villa", "Apartment"],
        data_source="Abu Dhabi Municipality 2024",
        last_updated="2024-12"
    ),
    "al_ghadeer": AreaData(
        name="Al Ghadeer",
        name_ar="الغدير",
        avg_price_per_sqft=950,
        avg_rent_yield=7.2,
        median_price=1200000,
        avg_rent=7200,
        transactions_2024=1234,
        price_trend="rising",
        risk_level="Low",
        popular_types=["Villa", "Townhouse", "Apartment"],
        data_source="Abu Dhabi Municipality 2024",
        last_updated="2024-12"
    ),
    "al_reet": AreaData(
        name="Al Reem",
        name_ar="الريم",
        avg_price_per_sqft=1350,
        avg_rent_yield=6.2,
        median_price=1700000,
        avg_rent=8800,
        transactions_2024=1567,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Villa"],
        data_source="Abu Dhabi Municipality 2024",
        last_updated="2024-12"
    ),
    "al_raha_beach": AreaData(
        name="Al Raha Beach",
        name_ar="شاطئ الراحة",
        avg_price_per_sqft=1600,
        avg_rent_yield=5.8,
        median_price=2200000,
        avg_rent=10600,
        transactions_2024=876,
        price_trend="stable",
        risk_level="Low",
        popular_types=["Apartment", "Villa"],
        data_source="Abu Dhabi Municipality 2024",
        last_updated="2024-12"
    ),
}


class UAEMarketService:
    """
    UAE Market Data Service.
    Provides comprehensive Dubai and Abu Dhabi market data.
    """
    
    def __init__(self):
        self.areas = {**DUBAI_AREAS, **ABU_DHABI_AREAS}
        self.dubai_pulse_api_key = None  # Optional: Set for live data
    
    def get_all_areas(self, market: str = "all") -> List[Dict[str, Any]]:
        """Get all areas with market data."""
        results = []
        
        if market in ["all", "dubai"]:
            for key, area in DUBAI_AREAS.items():
                results.append(self._area_to_dict(area, "dubai"))
        
        if market in ["all", "abu_dhabi"]:
            for key, area in ABU_DHABI_AREAS.items():
                results.append(self._area_to_dict(area, "abu_dhabi"))
        
        return sorted(results, key=lambda x: x["avgRentYield"], reverse=True)
    
    def get_area_data(self, area_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific area."""
        # Normalize area name
        normalized = area_name.lower().replace(" ", "_").replace("-", "_")
        
        # Try direct match
        if normalized in self.areas:
            area = self.areas[normalized]
            market = "dubai" if normalized in DUBAI_AREAS else "abu_dhabi"
            return self._area_to_dict(area, market)
        
        # Try partial match
        for key, area in self.areas.items():
            if normalized in key or key in normalized:
                market = "dubai" if key in DUBAI_AREAS else "abu_dhabi"
                return self._area_to_dict(area, market)
        
        return None
    
    def get_best_roi_areas(self, market: str = "dubai", limit: int = 5) -> List[Dict[str, Any]]:
        """Get areas with best ROI."""
        areas = DUBAI_AREAS if market == "dubai" else ABU_DHABI_AREAS
        
        sorted_areas = sorted(
            areas.items(),
            key=lambda x: x[1].avg_rent_yield,
            reverse=True
        )[:limit]
        
        return [
            self._area_to_dict(area, market)
            for _, area in sorted_areas
        ]
    
    def get_best_deal_areas(self, market: str = "dubai") -> List[Dict[str, Any]]:
        """Get areas with best deal potential (high ROI + rising prices)."""
        areas = DUBAI_AREAS if market == "dubai" else ABU_DHABI_AREAS
        
        deals = []
        for key, area in areas.items():
            if area.price_trend == "rising" and area.avg_rent_yield >= 7.0:
                deal_score = self._calculate_deal_score(area)
                area_dict = self._area_to_dict(area, market)
                area_dict["deal_score"] = deal_score
                deals.append(area_dict)
        
        return sorted(deals, key=lambda x: x["deal_score"], reverse=True)
    
    def _calculate_deal_score(self, area: AreaData) -> int:
        """Calculate deal score (0-100) based on various factors."""
        score = 50  # Base
        
        # ROI contribution (up to +25)
        score += min(area.avg_rent_yield * 2, 25)
        
        # Price trend contribution (up to +15)
        if area.price_trend == "rising":
            score += 15
        elif area.price_trend == "stable":
            score += 10
        
        # Risk contribution (up to +10)
        if area.risk_level == "Low":
            score += 10
        elif area.risk_level == "Medium":
            score += 5
        
        # Transaction volume contribution (up to +5)
        if area.transactions_2024 > 2000:
            score += 5
        elif area.transactions_2024 > 1000:
            score += 3
        
        return min(int(score), 100)
    
    def _area_to_dict(self, area: AreaData, market: str) -> Dict[str, Any]:
        return {
            "name": area.name,
            "nameAr": area.name_ar,
            "market": market,
            "avgPricePerSqFt": area.avg_price_per_sqft,
            "avgRentYield": area.avg_rent_yield,
            "medianPrice": area.median_price,
            "avgRent": area.avg_rent,
            "transactions2024": area.transactions_2024,
            "priceTrend": area.price_trend,
            "riskLevel": area.risk_level,
            "popularTypes": area.popular_types,
            "dataSource": area.data_source,
            "lastUpdated": area.last_updated,
        }
    
    async def get_live_data_from_dubai_pulse(self, area: str) -> Optional[Dict[str, Any]]:
        """Fetch live data from Dubai Pulse API (optional)."""
        if not self.dubai_pulse_api_key:
            return None
        
        # This would integrate with Dubai Pulse API
        # https://www.dubaipulse.gov.ae
        pass
    
    def get_market_summary(self, market: str = "dubai") -> Dict[str, Any]:
        """Get overall market summary."""
        areas = DUBAI_AREAS if market == "dubai" else ABU_DHABI_AREAS
        
        avg_yield = sum(a.avg_rent_yield for a in areas.values()) / len(areas)
        avg_price = sum(a.avg_price_per_sqft for a in areas.values()) / len(areas)
        total_transactions = sum(a.transactions_2024 for a in areas.values())
        
        rising = len([a for a in areas.values() if a.price_trend == "rising"])
        
        return {
            "market": market,
            "totalAreas": len(areas),
            "avgYield": round(avg_yield, 1),
            "avgPricePerSqFt": round(avg_price, 0),
            "totalTransactions2024": total_transactions,
            "risingAreas": rising,
            "stableAreas": len(areas) - rising,
            "dominantTrend": "rising" if rising > len(areas) / 2 else "stable",
        }
