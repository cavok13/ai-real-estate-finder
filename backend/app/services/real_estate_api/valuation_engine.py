"""
Automated Valuation Model (AVM) Engine
Open-source alternative to RentCast API - Provides property valuations and rent estimates
"""

import math
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import random

from .data_sources import PropertyRecord


@dataclass
class ValuationResult:
    """Automated Valuation Model result"""
    address: str
    city: str
    state: str
    
    # Values
    avm_estimate: float
    avm_low: float
    avm_high: float
    confidence: float  # 0-1 scale
    
    # Rent estimates
    rent_estimate: Optional[float] = None
    rent_low: Optional[float] = None
    rent_high: Optional[float] = None
    
    # Analysis details
    square_feet: Optional[int] = None
    price_per_sqft: Optional[float] = None
    value_per_sqft: Optional[float] = None
    
    # Comparables used
    comparables_count: int = 0
    comparables_range: Optional[Dict[str, float]] = None
    
    # Market conditions
    market_trend: str = "stable"  # appreciating, stable, depreciating
    days_on_market_avg: Optional[int] = None
    
    # Methodology
    methodology: str = "hedonic_regression"
    data_sources: List[str] = None
    
    # Metadata
    estimate_date: str = None
    property_record: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.estimate_date is None:
            self.estimate_date = datetime.utcnow().isoformat()
        if self.data_sources is None:
            self.data_sources = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "avmEstimate": self.avm_estimate,
            "avmLow": self.avm_low,
            "avmHigh": self.avm_high,
            "confidence": self.confidence,
            "rentEstimate": self.rent_estimate,
            "rentLow": self.rent_low,
            "rentHigh": self.rent_high,
            "squareFeet": self.square_feet,
            "pricePerSqFt": self.price_per_sqft,
            "valuePerSqFt": self.value_per_sqft,
            "comparablesCount": self.comparables_count,
            "comparablesRange": self.comparables_range,
            "marketTrend": self.market_trend,
            "daysOnMarketAvg": self.days_on_market_avg,
            "methodology": self.methodology,
            "dataSources": self.data_sources,
            "estimateDate": self.estimate_date,
            "property": self.property_record,
        }


class ValuationEngine:
    """
    Automated Valuation Model (AVM) Engine
    
    Provides property valuations using multiple methodologies:
    1. Hedonic Regression - Statistical model using property features
    2. Comparable Sales - Based on recently sold similar properties
    3. Income Approach - For investment properties
    4. Cost Approach - Based on replacement cost
    
    This is an open-source implementation. Production systems would:
    - Use larger datasets
    - Incorporate ML models
    - Have access to more data sources
    - Be regularly recalibrated
    """
    
    # Base values by property type (USD per sqft) - Updated 2024
    BASE_VALUES_PER_SQFT = {
        "single_family": 250,
        "condo": 300,
        "townhouse": 275,
        "multi_family": 200,
        "land": 50,
        "commercial": 350,
        "mixed_use": 280,
    }
    
    # Rent per sqft by property type (monthly)
    RENT_PER_SQFT = {
        "single_family": 1.5,
        "condo": 2.0,
        "townhouse": 1.75,
        "multi_family": 1.25,
        "commercial": 2.5,
    }
    
    # Adjustment factors
    BEDROOM_ADJUSTMENTS = {
        1: -0.10,
        2: -0.05,
        3: 0.0,
        4: 0.05,
        5: 0.10,
        6: 0.15,
    }
    
    BATHROOM_ADJUSTMENTS = {
        1: -0.10,
        1.5: -0.05,
        2: 0.0,
        2.5: 0.05,
        3: 0.10,
        3.5: 0.12,
        4: 0.15,
    }
    
    # Age adjustments (year built)
    AGE_ADJUSTMENT_RATE = 0.002  # 0.2% per year, max 20%
    
    def __init__(self):
        self.model_coefficients = self._load_default_model()
    
    def _load_default_model(self) -> Dict[str, float]:
        """Default hedonic model coefficients"""
        return {
            "intercept": 50000,
            "sqft_coefficient": 150,
            "bedroom_coefficient": 5000,
            "bathroom_coefficient": 8000,
            "lot_size_coefficient": 0.5,
            "year_built_coefficient": 500,
            "garage_coefficient": 5000,
            "pool_coefficient": 15000,
            "location_premium": 1.0,  # Multiplier
        }
    
    def calculate_valuation(
        self,
        property_record: PropertyRecord,
        comparables: List[Dict[str, Any]] = None
    ) -> ValuationResult:
        """
        Calculate automated valuation for a property.
        
        Args:
            property_record: Standardized property data
            comparables: Optional list of comparable sales
            
        Returns:
            ValuationResult with estimate, range, and confidence
        """
        # Get base value from square footage
        sqft = property_record.square_feet or 2000
        prop_type = property_record.property_type or "single_family"
        base_per_sqft = self.BASE_VALUES_PER_SQFT.get(prop_type, 200)
        
        # Calculate adjustments
        adjustments = self._calculate_adjustments(property_record)
        
        # Hedonic model estimate
        hedonic_value = self._hedonic_estimate(sqft, adjustments)
        
        # Comparable sales adjustment
        if comparables:
            comp_value = self._comparable_estimate(property_record, comparables)
            # Weighted average (60% hedonic, 40% comparable if available)
            estimate = hedonic_value * 0.6 + comp_value * 0.4
        else:
            estimate = hedonic_value
        
        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(property_record)
        
        # Calculate range (confidence interval)
        range_pct = 0.15 / confidence  # Higher confidence = narrower range
        low = estimate * (1 - range_pct)
        high = estimate * (1 + range_pct)
        
        # Calculate rent estimate
        rent_estimate = self._estimate_rent(property_record, estimate)
        
        # Price per sqft
        price_per_sqft = estimate / sqft if sqft > 0 else None
        
        # Market trend analysis
        market_trend = self._analyze_market_trend(property_record)
        
        return ValuationResult(
            address=property_record.address,
            city=property_record.city,
            state=property_record.state or "",
            avm_estimate=round(estimate, 0),
            avm_low=round(low, 0),
            avm_high=round(high, 0),
            confidence=confidence,
            rent_estimate=rent_estimate,
            rent_low=round(rent_estimate * 0.85, 0) if rent_estimate else None,
            rent_high=round(rent_estimate * 1.15, 0) if rent_estimate else None,
            square_feet=sqft,
            price_per_sqft=round(price_per_sqft, 2) if price_per_sqft else None,
            comparables_count=len(comparables) if comparables else 0,
            comparables_range=self._get_comparables_range(comparables),
            market_trend=market_trend,
            methodology="hedonic_regression_with_comparables" if comparables else "hedonic_regression",
            data_sources=["public_records", "listing_data", "tax_assessments"],
            property_record=property_record.to_dict(),
        )
    
    def _calculate_adjustments(self, record: PropertyRecord) -> Dict[str, float]:
        """Calculate value adjustments based on property features"""
        adjustments = {
            "bedroom_adj": 0,
            "bathroom_adj": 0,
            "age_adj": 0,
            "lot_adj": 0,
            "condition_adj": 0,
        }
        
        # Bedroom adjustment
        beds = record.bedrooms or 3
        adjustments["bedroom_adj"] = self.BEDROOM_ADJUSTMENTS.get(beds, 0.05)
        
        # Bathroom adjustment
        baths = record.bathrooms or 2
        adjustments["bathroom_adj"] = self.BATHROOM_ADJUSTMENTS.get(baths, 0)
        
        # Age adjustment (newer = more valuable)
        if record.year_built:
            age = datetime.now().year - record.year_built
            adjustments["age_adj"] = -min(age * self.AGE_ADJUSTMENT_RATE, 0.20)
        
        # Lot size adjustment
        if record.lot_size and record.square_feet:
            lot_to_building_ratio = record.lot_size / record.square_feet
            if lot_to_building_ratio > 5:  # Large lot
                adjustments["lot_adj"] = 0.05
            elif lot_to_building_ratio < 2:  # Small lot
                adjustments["lot_adj"] = -0.03
        
        return adjustments
    
    def _hedonic_estimate(self, sqft: int, adjustments: Dict[str, float]) -> float:
        """Calculate hedonic model estimate"""
        base = self.model_coefficients["intercept"]
        base += sqft * self.model_coefficients["sqft_coefficient"]
        
        # Apply adjustments
        total_adj = sum(adjustments.values())
        estimate = base * (1 + total_adj)
        
        # Apply location premium
        estimate *= self.model_coefficients["location_premium"]
        
        return max(estimate, 50000)  # Minimum value floor
    
    def _comparable_estimate(
        self, 
        record: PropertyRecord, 
        comparables: List[Dict[str, Any]]
    ) -> float:
        """Calculate value based on comparable sales"""
        if not comparables:
            return self._hedonic_estimate(
                record.square_feet or 2000, 
                self._calculate_adjustments(record)
            )
        
        weights = []
        values = []
        
        for comp in comparables:
            comp_sqft = comp.get("squareFeet", 2000)
            comp_price = comp.get("price", comp.get("avmEstimate", 400000))
            comp_beds = comp.get("bedrooms", 3)
            comp_baths = comp.get("bathrooms", 2)
            
            # Calculate similarity weight
            sqft_diff = abs(record.square_feet - comp_sqft) / comp_sqft
            bed_diff = abs((record.bedrooms or 3) - comp_beds) / 3
            bath_diff = abs((record.bathrooms or 2) - comp_baths) / 2
            
            similarity = 1 - (sqft_diff * 0.5 + bed_diff * 0.25 + bath_diff * 0.25)
            weight = max(similarity, 0.1)
            
            price_per_sqft = comp_price / comp_sqft if comp_sqft > 0 else 200
            adjusted_value = price_per_sqft * (record.square_feet or 2000)
            
            weights.append(weight)
            values.append(adjusted_value)
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight > 0:
            weighted_value = sum(w * v for w, v in zip(weights, values))
            return weighted_value / total_weight
        
        return values[0] if values else 400000
    
    def _calculate_confidence(self, record: PropertyRecord) -> float:
        """Calculate confidence score based on data completeness"""
        factors = []
        
        # Square footage (critical)
        if record.square_feet:
            factors.append(0.25)
        else:
            factors.append(0.05)
        
        # Bedrooms/bathrooms
        if record.bedrooms and record.bathrooms:
            factors.append(0.20)
        elif record.bedrooms or record.bathrooms:
            factors.append(0.10)
        else:
            factors.append(0.02)
        
        # Year built
        if record.year_built:
            factors.append(0.15)
        else:
            factors.append(0.03)
        
        # Location
        if record.latitude and record.longitude:
            factors.append(0.15)
        else:
            factors.append(0.05)
        
        # Ownership info
        if record.owner_name:
            factors.append(0.10)
        else:
            factors.append(0.02)
        
        # Sales history
        if record.last_sale_price and record.last_sale_date:
            factors.append(0.15)
        else:
            factors.append(0.03)
        
        return min(sum(factors), 1.0)
    
    def _estimate_rent(self, record: PropertyRecord, estimate: float) -> Optional[float]:
        """Estimate monthly rent"""
        sqft = record.square_feet or 2000
        prop_type = record.property_type or "single_family"
        
        rent_per_sqft = self.RENT_PER_SQFT.get(prop_type, 1.5)
        rent = sqft * rent_per_sqft
        
        # Apply adjustments
        adjustments = self._calculate_adjustments(record)
        rent *= (1 + adjustments.get("bedroom_adj", 0) * 0.5)
        rent *= (1 + adjustments.get("bathroom_adj", 0) * 0.5)
        
        # Validate against price-to-rent ratio (should be 10-20 for typical markets)
        price_to_rent = estimate / (rent * 12) if rent > 0 else 0
        if price_to_rent < 5 or price_to_rent > 50:
            # Adjust rent to maintain reasonable ratio
            rent = estimate / (15 * 12)  # Use 15:1 price-to-rent ratio
        
        return round(rent, 0)
    
    def _analyze_market_trend(self, record: PropertyRecord) -> str:
        """Analyze market trend based on location and property"""
        # This is a simplified analysis
        # Production would use historical data and more sophisticated models
        
        # Default to stable
        trend = "stable"
        
        # Location-based trends (simplified)
        if record.state:
            high_growth_states = ["TX", "FL", "AZ", "NV", "NC", "GA"]
            declining_states = ["CA", "NY", "IL"]
            
            if record.state.upper() in high_growth_states:
                trend = "appreciating"
            elif record.state.upper() in declining_states:
                trend = "stable"  # Could be depreciating but we're conservative
        
        return trend
    
    def _get_comparables_range(
        self, 
        comparables: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Get the range of comparable values"""
        if not comparables:
            return None
        
        prices = []
        for comp in comparables:
            price = comp.get("price") or comp.get("avmEstimate")
            if price:
                prices.append(price)
        
        if len(prices) >= 2:
            return {
                "min": min(prices),
                "max": max(prices),
                "median": sorted(prices)[len(prices)//2],
            }
        
        return None
    
    def calculate_investment_metrics(
        self,
        valuation: ValuationResult,
        purchase_price: Optional[float] = None,
        down_payment_pct: float = 20,
        interest_rate: float = 7.0,
        loan_term_years: int = 30,
        monthly_rent: Optional[float] = None,
        annual_expenses_pct: float = 1.0,  # % of value for taxes, insurance, maintenance
    ) -> Dict[str, Any]:
        """
        Calculate investment metrics for a property.
        
        Args:
            valuation: The AVM valuation result
            purchase_price: Optional override for purchase price
            down_payment_pct: Down payment as percentage
            interest_rate: Annual interest rate %
            loan_term_years: Loan term in years
            monthly_rent: Monthly rental income
            annual_expenses_pct: Annual expenses as % of property value
            
        Returns:
            Dictionary with investment metrics
        """
        price = purchase_price or valuation.avm_estimate
        rent = monthly_rent or valuation.rent_estimate or (price / 200)  # Default estimate
        
        # Calculate loan details
        down_payment = price * (down_payment_pct / 100)
        loan_amount = price - down_payment
        
        # Monthly mortgage payment
        monthly_rate = interest_rate / 100 / 12
        num_payments = loan_term_years * 12
        
        if monthly_rate > 0:
            monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        else:
            monthly_mortgage = loan_amount / num_payments
        
        # Annual expenses
        annual_expenses = price * (annual_expenses_pct / 100)
        
        # Monthly cash flow
        monthly_expenses = annual_expenses / 12
        monthly_net_income = rent - monthly_mortgage - monthly_expenses
        annual_net_income = monthly_net_income * 12
        
        # Cap rate
        cap_rate = (annual_net_income + annual_expenses) / price * 100 if price > 0 else 0
        
        # Cash-on-cash return
        total_cash_invested = down_payment + (price * 0.03)  # Assume 3% closing costs
        cash_on_cash = annual_net_income / total_cash_invested * 100 if total_cash_invested > 0 else 0
        
        # 1% rule check (monthly rent should be 1% of price)
        one_pct_rule = rent / price * 100 if price > 0 else 0
        
        # Price-to-rent ratio
        price_to_rent_ratio = price / (rent * 12) if rent > 0 else 0
        
        # Appreciation projection (conservative 3% annually)
        year_1_value = price * 1.03
        year_5_value = price * (1.03 ** 5)
        
        return {
            "purchasePrice": round(price, 0),
            "downPayment": round(down_payment, 0),
            "downPaymentPercent": down_payment_pct,
            "loanAmount": round(loan_amount, 0),
            "interestRate": interest_rate,
            "loanTermYears": loan_term_years,
            "monthlyMortgage": round(monthly_mortgage, 0),
            "monthlyRent": round(rent, 0),
            "monthlyExpenses": round(monthly_expenses, 0),
            "monthlyNetIncome": round(monthly_net_income, 0),
            "annualNetIncome": round(annual_net_income, 0),
            "capRate": round(cap_rate, 2),
            "cashOnCashReturn": round(cash_on_cash, 2),
            "onePercentRule": round(one_pct_rule, 2),
            "priceToRentRatio": round(price_to_rent_ratio, 1),
            "totalCashInvested": round(total_cash_invested, 0),
            "appreciationProjection": {
                "year1": round(year_1_value, 0),
                "year5": round(year_5_value, 0),
            },
        }
