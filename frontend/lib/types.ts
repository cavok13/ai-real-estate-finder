export interface User {
  id: number;
  email: string;
  full_name: string | null;
  credits: number;
  is_premium: boolean;
  referral_code: string;
  created_at: string;
}

export interface Property {
  id: number;
  title: string;
  price: number;
  area: number;
  price_per_m2: number | null;
  location: string | null;
  district: string | null;
  city: string;
  country: string;
  currency: string;
  currency_symbol: string;
  region: string | null;
  property_type: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  latitude: number | null;
  longitude: number | null;
  image_url: string | null;
  created_at: string;
}

export interface PropertyWithScore extends Property {
  deal_score: number;
  price_vs_market: number;
  recommendation: string;
}

export interface AnalysisRequest {
  budget_min?: number;
  budget_max?: number;
  preferred_city?: string;
  property_type?: string;
  bedrooms_min?: number;
}

export interface AnalysisResponse {
  id: number;
  deal_score: number;
  price_vs_market: number;
  recommendation: string;
  insights: {
    total_properties_found: number;
    market_average_score: number;
    best_deal_score: number;
    price_range: {
      min: number;
      max: number;
    };
    area_insights: string[];
  };
  top_properties: PropertyWithScore[];
  created_at: string;
}

export interface CreditPackage {
  id: string;
  credits: number;
  price_cents: number;
  price_display: string;
}

export interface DashboardStats {
  total_analyses: number;
  credits_remaining: number;
  top_deal_score: number | null;
  recent_analyses: AnalysisResponse[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  referral_code?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
