const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: string;
  email: string;
  is_email_verified: boolean;
  plan: string;
  free_credits: number;
  paid_credits: number;
  total_credits: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function getDeviceFingerprint(): Promise<string> {
  if (typeof window === "undefined") return "server";
  const raw = [
    navigator.userAgent,
    navigator.language,
    window.screen.width,
    window.screen.height,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    navigator.platform,
  ].join("|");
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(raw));
  const bytes = Array.from(new Uint8Array(buf));
  return bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  if (typeof window !== "undefined") {
    headers["x-device-fingerprint"] = await getDeviceFingerprint();
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let message = `Error ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) message = data.detail;
    } catch {}
    throw new Error(message);
  }

  return res.json();
}

export async function registerUser(
  email: string,
  password: string,
  captchaToken?: string | null
) {
  return apiFetch<{ message: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, captcha_token: captchaToken || null }),
  });
}

export async function verifyEmail(token: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(token: string): Promise<User> {
  return apiFetch<User>("/me", { method: "GET" }, token);
}

export interface AnalysisRequest {
  property_url: string;
  title?: string | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
  property_type?: string | null;
  price?: number | null;
  rent_estimate?: number | null;
  area_sqm?: number | null;
  bedrooms?: number | null;
  bathrooms?: number | null;
  roi?: number | null;
  deal_score?: number | null;
  risk_level?: string | null;
  market_delta_pct?: number | null;
  notes?: string | null;
  extra_data?: Record<string, unknown>;
}

export interface AnalysisResponse {
  cached: boolean;
  provider: string;
  model: string;
  remaining_credits: number;
  credit_source: string | null;
  analysis: {
    headline: string;
    summary: string;
    strengths: string[];
    risks: string[];
    decision: "BUY" | "REVIEW" | "AVOID" | string;
    score_explanation: string;
    next_step: string;
    [key: string]: unknown;
  };
}

export async function analyzeProperty(
  token: string,
  payload: AnalysisRequest
): Promise<AnalysisResponse> {
  return apiFetch<AnalysisResponse>(
    "/analysis",
    { method: "POST", body: JSON.stringify(payload) },
    token
  );
}

export interface DealCandidate {
  id: string;
  country?: string | null;
  city?: string | null;
  price?: number | null;
  currency?: string | null;
  price_per_sqm?: number | null;
  gross_yield?: number | null;
  url?: string | null;
  source?: string | null;
  score?: number | null;
  raw: Record<string, unknown>;
}

export interface SearchDealsResponse {
  provider: string;
  model: string;
  remaining_credits: number;
  credit_source: string | null;
  search_params: Record<string, unknown>;
  ai_summary: {
    strategy_summary: string;
    best_deals: {
      id: string;
      headline: string;
      why_good: string;
      risks: string;
      decision: string;
      suggested_strategy: string;
    }[];
    diversified_plan: unknown;
    [key: string]: unknown;
  };
  deals: DealCandidate[];
}

export async function searchDeals(
  token: string,
  body: {
    budget_min: number;
    budget_max: number;
    currency: string;
    countries: string[];
    cities: string[];
    strategy: "rental_yield" | "capital_growth" | "balanced";
    limit: number;
  }
): Promise<SearchDealsResponse> {
  return apiFetch<SearchDealsResponse>(
    "/search-deals",
    { method: "POST", body: JSON.stringify(body) },
    token
  );
}

export async function createCheckoutSession(
  token: string,
  plan: "starter" | "pro"
): Promise<{ checkout_url: string }> {
  return apiFetch<{ checkout_url: string }>(
    "/billing/checkout",
    { method: "POST", body: JSON.stringify({ plan }) },
    token
  );
}
