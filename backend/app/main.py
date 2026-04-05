import os
import json
import hashlib
import secrets
import smtplib
from uuid import uuid4
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional, Any, List, Literal

import httpx
import stripe
from jose import jwt, JWTError
from openai import AsyncOpenAI
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ─── Config ───────────────────────────────────────────────────────────────────

APP_NAME = os.getenv("APP_NAME", "AI Deals Finder API")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = [
    x.strip()
    for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if x.strip()
]

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_deals_finder.db")

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_to_a_long_random_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

FREE_TRIAL_CREDITS = int(os.getenv("FREE_TRIAL_CREDITS", "3"))
ANALYSIS_CACHE_HOURS = int(os.getenv("ANALYSIS_CACHE_HOURS", "72"))
MAX_SIGNUPS_PER_IP_PER_HOUR = int(os.getenv("MAX_SIGNUPS_PER_IP_PER_HOUR", "5"))
MAX_TRIALS_PER_IP = int(os.getenv("MAX_TRIALS_PER_IP", "1"))
MAX_ANALYSES_PER_USER_PER_MINUTE = int(os.getenv("MAX_ANALYSES_PER_USER_PER_MINUTE", "5"))
MAX_ANALYSES_PER_IP_PER_MINUTE = int(os.getenv("MAX_ANALYSES_PER_IP_PER_MINUTE", "15"))

DISPOSABLE_DOMAINS = {
    x.strip().lower()
    for x in os.getenv(
        "DISPOSABLE_DOMAINS",
        "mailinator.com,tempmail.com,10minutemail.com,guerrillamail.com,yopmail.com",
    ).split(",")
    if x.strip()
}

TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "").strip()

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@yourdomain.com").strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "AI Deals Finder").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

HF_API_KEY = os.getenv("HF_API_KEY", "").strip()
HF_BASE_URL = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1").strip()
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct:cerebras").strip()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "").strip()
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "").strip()
STARTER_MONTHLY_CREDITS = int(os.getenv("STARTER_MONTHLY_CREDITS", "100"))
PRO_MONTHLY_CREDITS = int(os.getenv("PRO_MONTHLY_CREDITS", "500"))

RENCAST_API_KEY = os.getenv("RENCAST_API_KEY", "").strip()
RENCAST_BASE_URL = os.getenv("RENCAST_BASE_URL", "https://api.rentcast.io/v1").strip()

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "").strip()
APIFY_GLOBAL_PROPERTY_SEARCH_ACTOR_ID = os.getenv(
    "APIFY_GLOBAL_PROPERTY_SEARCH_ACTOR_ID",
    "wonderful_beluga~global-property-search",
).strip()

stripe.api_key = STRIPE_SECRET_KEY or None

# ─── Auth helpers ─────────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ─── Database ─────────────────────────────────────────────────────────────────

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign",
    "utm_term", "utm_content", "fbclid", "gclid",
}


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid4())


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_id)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)

    plan = Column(String, default="free", nullable=False)
    free_credits = Column(Integer, default=0, nullable=False)
    paid_credits = Column(Integer, default=0, nullable=False)

    trial_eligible = Column(Boolean, default=True, nullable=False)
    trial_granted = Column(Boolean, default=False, nullable=False)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    signup_ip = Column(String, nullable=True, index=True)
    signup_fingerprint = Column(String, nullable=True, index=True)

    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SignupAttempt(Base):
    __tablename__ = "signup_attempts"

    id = Column(String, primary_key=True, default=new_id)
    email = Column(String, nullable=True, index=True)
    ip = Column(String, nullable=True, index=True)
    fingerprint = Column(String, nullable=True, index=True)
    success = Column(Boolean, default=False, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class LoginEvent(Base):
    __tablename__ = "login_events"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ip = Column(String, nullable=True, index=True)
    fingerprint = Column(String, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    id = Column(String, primary_key=True, default=new_id)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    normalized_url = Column(Text, nullable=False, index=True)
    response_text = Column(Text, nullable=False)
    response_json = Column(JSON, nullable=False)
    provider_used = Column(String, nullable=False)
    model_used = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    property_url = Column(Text, nullable=False)
    normalized_url = Column(Text, nullable=False, index=True)
    cache_key = Column(String, nullable=False, index=True)

    provider_used = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    credits_charged = Column(Integer, default=0, nullable=False)
    credit_source = Column(String, nullable=True)
    cached = Column(Boolean, default=False, nullable=False)

    raw_request = Column(JSON, nullable=False)
    response_text = Column(Text, nullable=False)
    response_json = Column(JSON, nullable=False)

    ip = Column(String, nullable=True, index=True)
    fingerprint = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class DealsSearchJob(Base):
    __tablename__ = "deals_search_jobs"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    search_params = Column(JSON, nullable=False)
    candidates = Column(JSON, nullable=False)
    ai_summary = Column(JSON, nullable=False)

    provider_used = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    credits_charged = Column(Integer, default=0, nullable=False)
    credit_source = Column(String, nullable=True)

    ip = Column(String, nullable=True, index=True)
    fingerprint = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    captcha_token: Optional[str] = None


class VerifyEmailIn(BaseModel):
    token: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PropertyAnalysisIn(BaseModel):
    property_url: str
    title: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    rent_estimate: Optional[float] = None
    area_sqm: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    roi: Optional[float] = None
    deal_score: Optional[float] = None
    risk_level: Optional[str] = None
    market_delta_pct: Optional[float] = None
    notes: Optional[str] = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class CheckoutIn(BaseModel):
    plan: str


class SearchDealsIn(BaseModel):
    budget_min: float = Field(gt=0)
    budget_max: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    countries: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)
    strategy: Literal["rental_yield", "capital_growth", "balanced"] = "balanced"
    limit: int = Field(default=10, ge=1, le=50)


class DealCandidateOut(BaseModel):
    id: str
    country: Optional[str] = None
    city: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    price_per_sqm: Optional[float] = None
    gross_yield: Optional[float] = None
    url: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    raw: dict[str, Any]


class SearchDealsOut(BaseModel):
    provider: str
    model: str
    remaining_credits: int
    credit_source: Optional[str]
    search_params: dict[str, Any]
    ai_summary: dict[str, Any]
    deals: List[DealCandidateOut]


class UserOut(BaseModel):
    id: str
    email: EmailStr
    is_email_verified: bool
    plan: str
    free_credits: int
    paid_credits: int
    total_credits: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str


class AnalysisOut(BaseModel):
    cached: bool
    provider: str
    model: str
    remaining_credits: int
    credit_source: Optional[str]
    analysis: dict[str, Any]


class CheckoutOut(BaseModel):
    checkout_url: str


# ─── DB dependency ────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Security helpers ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Missing subject")
    return str(sub)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(48)


# ─── Credit helpers ───────────────────────────────────────────────────────────

def total_credits(user: User) -> int:
    return max(0, user.free_credits) + max(0, user.paid_credits)


def grant_trial_credits(user: User):
    if not user.trial_granted:
        user.free_credits += FREE_TRIAL_CREDITS
        user.trial_granted = True


def consume_one_credit(user: User) -> str:
    if user.free_credits > 0:
        user.free_credits -= 1
        return "free"
    if user.paid_credits > 0:
        user.paid_credits -= 1
        return "paid"
    raise ValueError("No credits available")


def refill_plan_credits(user: User, plan: str):
    user.plan = plan
    if plan == "starter":
        user.paid_credits = STARTER_MONTHLY_CREDITS
    elif plan == "pro":
        user.paid_credits = PRO_MONTHLY_CREDITS
    else:
        user.plan = "free"
        user.paid_credits = 0


# ─── URL normalization ────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k not in TRACKING_PARAMS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunparse((scheme, netloc, path, "", query, ""))


def payload_to_dict(payload: PropertyAnalysisIn) -> dict[str, Any]:
    data = payload.model_dump(exclude_none=True)
    data["property_url"] = normalize_url(data["property_url"])
    return data


def build_cache_key(payload_dict: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload_dict, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─── AI prompt builders ───────────────────────────────────────────────────────

def build_prompt_messages(payload_dict: dict[str, Any]) -> list[dict[str, str]]:
    compact = json.dumps(payload_dict, ensure_ascii=False, sort_keys=True, indent=2)
    system = (
        "You are a senior real-estate investment analyst.\n"
        "Return strict JSON only.\n"
        "Required keys:\n"
        "- headline\n"
        "- summary\n"
        "- strengths\n"
        "- risks\n"
        "- decision\n"
        "- score_explanation\n"
        "- next_step\n"
        "Rules:\n"
        "- strengths and risks must be arrays of short strings\n"
        "- decision must be one of BUY, REVIEW, AVOID\n"
        "- Use only the provided facts\n"
        "- Do not invent external market data\n"
        "- Keep the summary concise and investor-focused"
    )
    user = (
        "Analyze this property for an investor.\n"
        "Focus on deal quality, ROI meaning, risk, and practical next step.\n"
        f"Property data:\n{compact}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_deals_messages(
    search_params: dict[str, Any],
    candidates: List[dict[str, Any]],
) -> list[dict[str, str]]:
    top_candidates = candidates[:20]
    params_json = json.dumps(search_params, ensure_ascii=False, sort_keys=True, indent=2)
    deals_json = json.dumps(top_candidates, ensure_ascii=False, sort_keys=True, indent=2)

    system = (
        "You are a senior global real-estate investment advisor.\n"
        "The user wants to find the best property deals worldwide within their budget.\n"
        "Return STRICT JSON only.\n"
        "Required keys:\n"
        "- strategy_summary\n"
        "- best_deals\n"
        "- diversified_plan\n"
        "In best_deals, each object must contain:\n"
        "- id\n"
        "- headline\n"
        "- why_good\n"
        "- risks\n"
        "- decision (BUY, WATCH, AVOID)\n"
        "- suggested_strategy\n"
        "Use ONLY the provided candidate data.\n"
        "Do NOT invent cities, prices, or yields.\n"
        "Be concise and investor-focused."
    )

    user = (
        "The user asked for the best global property deals within a budget and filters.\n"
        "First, understand the search parameters.\n"
        "Then, pick and explain the top deals that best match.\n"
        "Search parameters:\n"
        f"{params_json}\n\n"
        "Candidate deals (already scored and normalized by the engine):\n"
        f"{deals_json}\n"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ─── JSON extractor ───────────────────────────────────────────────────────────

def extract_json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return {
        "headline": "Property Analysis",
        "summary": text[:1200] if text else "No valid JSON returned by the model.",
        "strengths": [],
        "risks": [],
        "decision": "REVIEW",
        "score_explanation": "Provider returned non-JSON output; response was normalized safely.",
        "next_step": "Review source data and rerun the analysis if needed.",
    }


# ─── Security / validation helpers ───────────────────────────────────────────

def sanitize_email(email: str) -> str:
    return email.lower().strip()


def is_disposable_email(email: str) -> bool:
    domain = email.split("@")[-1].lower().strip()
    return domain in DISPOSABLE_DOMAINS


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def get_device_fingerprint(request: Request) -> str:
    header_fp = request.headers.get("x-device-fingerprint", "").strip()
    if header_fp:
        return header_fp[:255]
    raw = "|".join([
        request.headers.get("user-agent", ""),
        request.headers.get("accept-language", ""),
        request.headers.get("sec-ch-ua-platform", ""),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def verify_turnstile(
    captcha_token: Optional[str], remote_ip: Optional[str] = None
) -> bool:
    if not TURNSTILE_SECRET_KEY:
        return True
    if not captcha_token:
        return False
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET_KEY,
                "response": captcha_token,
                "remoteip": remote_ip or "",
            },
        )
        data = response.json()
        return bool(data.get("success"))


def log_signup_attempt(
    db: Session,
    email: str,
    ip: str,
    fingerprint: str,
    success: bool,
    reason: Optional[str],
):
    row = SignupAttempt(
        email=email,
        ip=ip,
        fingerprint=fingerprint,
        success=success,
        reason=reason,
    )
    db.add(row)
    db.commit()


def can_register_from_ip(db: Session, ip: str) -> bool:
    window = utcnow() - timedelta(hours=1)
    count = (
        db.query(SignupAttempt)
        .filter(SignupAttempt.ip == ip, SignupAttempt.created_at >= window)
        .count()
    )
    return count < MAX_SIGNUPS_PER_IP_PER_HOUR


def is_trial_eligible(db: Session, ip: str, fingerprint: str) -> bool:
    same_fp = (
        db.query(User)
        .filter(User.signup_fingerprint == fingerprint, User.trial_granted.is_(True))
        .first()
    )
    if same_fp:
        return False
    same_ip_count = (
        db.query(User)
        .filter(User.signup_ip == ip, User.trial_granted.is_(True))
        .count()
    )
    return same_ip_count < MAX_TRIALS_PER_IP


def is_analysis_rate_limited(db: Session, user_id: str, ip: str) -> bool:
    window = utcnow() - timedelta(minutes=1)
    user_count = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.user_id == user_id, AnalysisJob.created_at >= window)
        .count()
    )
    ip_count = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.ip == ip, AnalysisJob.created_at >= window)
        .count()
    )
    return (
        user_count >= MAX_ANALYSES_PER_USER_PER_MINUTE
        or ip_count >= MAX_ANALYSES_PER_IP_PER_MINUTE
    )


# ─── Email ────────────────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, text_body: str):
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.set_content(text_body)

    if SMTP_USE_TLS and SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)


def send_verification_email(email: str, raw_token: str):
    verify_url = f"{FRONTEND_URL.rstrip('/')}/verify-email?token={raw_token}"
    body = (
        "Welcome to AI Deals Finder.\n\n"
        "Please verify your email by opening this link:\n"
        f"{verify_url}\n\n"
        "After verification, your free credits will be activated.\n"
        "If this was not you, ignore this email."
    )
    send_email(email, "Verify your AI Deals Finder account", body)


# ─── LLM providers ────────────────────────────────────────────────────────────

async def call_provider_openai_compatible(
    provider_name: str,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=900,
    )
    content = completion.choices[0].message.content or ""
    parsed = extract_json_from_text(content)
    return {
        "provider": provider_name,
        "model": model,
        "raw_text": content,
        "parsed": parsed,
    }


async def generate_analysis(payload_dict: dict[str, Any]) -> dict[str, Any]:
    messages = build_prompt_messages(payload_dict)
    errors = []

    providers = []
    if GROQ_API_KEY:
        providers.append({
            "name": "groq",
            "base_url": GROQ_BASE_URL,
            "api_key": GROQ_API_KEY,
            "model": GROQ_MODEL,
        })
    if HF_API_KEY:
        providers.append({
            "name": "huggingface",
            "base_url": HF_BASE_URL,
            "api_key": HF_API_KEY,
            "model": HF_MODEL,
        })

    if not providers:
        raise RuntimeError("No LLM provider configured. Set GROQ_API_KEY and/or HF_API_KEY.")

    for provider in providers:
        try:
            return await call_provider_openai_compatible(
                provider_name=provider["name"],
                base_url=provider["base_url"],
                api_key=provider["api_key"],
                model=provider["model"],
                messages=messages,
            )
        except Exception as exc:
            errors.append(f'{provider["name"]}: {str(exc)}')

    raise RuntimeError("All providers failed: " + " | ".join(errors))


async def generate_deals_summary(
    search_params: dict[str, Any],
    candidates: List[dict[str, Any]],
) -> dict[str, Any]:
    messages = build_deals_messages(search_params, candidates)
    errors: list[str] = []

    providers: list[dict[str, str]] = []
    if GROQ_API_KEY:
        providers.append({
            "name": "groq",
            "base_url": GROQ_BASE_URL,
            "api_key": GROQ_API_KEY,
            "model": GROQ_MODEL,
        })
    if HF_API_KEY:
        providers.append({
            "name": "huggingface",
            "base_url": HF_BASE_URL,
            "api_key": HF_API_KEY,
            "model": HF_MODEL,
        })

    if not providers:
        raise RuntimeError("No LLM provider configured for deals search.")

    for provider in providers:
        try:
            return await call_provider_openai_compatible(
                provider_name=provider["name"],
                base_url=provider["base_url"],
                api_key=provider["api_key"],
                model=provider["model"],
                messages=messages,
            )
        except Exception as exc:
            errors.append(f'{provider["name"]}: {str(exc)}')

    raise RuntimeError("All deals LLM providers failed: " + " | ".join(errors))


# ─── Property data fetchers ───────────────────────────────────────────────────

async def fetch_candidate_properties(
    search: SearchDealsIn,
) -> List[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    # ── RentCast (USA) ────────────────────────────────────────────────────────
    if RENCAST_API_KEY and any(
        c.upper() in {"US", "USA", "UNITED STATES"} for c in search.countries
    ):
        city = search.cities[0] if search.cities else None
        if city:
            params = {
                "city": city,
                "state": "CA",
                "status": "active",
                "limit": min(search.limit * 3, 50),
            }
            headers = {"X-Api-Key": RENCAST_API_KEY, "Accept": "application/json"}
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    res = await client.get(
                        f"{RENCAST_BASE_URL.rstrip('/')}/listings",
                        params=params,
                        headers=headers,
                    )
                    res.raise_for_status()
                    data = res.json()
                except Exception as exc:
                    data = []
                    print(f"RentCast error: {exc}")

            if isinstance(data, list):
                for item in data:
                    price = item.get("price") or item.get("list_price")
                    if price is None:
                        continue
                    if not (search.budget_min <= float(price) <= search.budget_max):
                        continue
                    sqft = item.get("living_area") or item.get("sqft")
                    price_per_sqm = None
                    if sqft:
                        try:
                            sqm = float(sqft) * 0.092903
                            if sqm > 0:
                                price_per_sqm = float(price) / sqm
                        except Exception:
                            pass
                    center = (search.budget_min + search.budget_max) / 2
                    span = max(search.budget_max - search.budget_min, 1.0)
                    distance = abs(float(price) - center) / span
                    score = max(0.0, 100.0 - distance * 40.0)
                    candidates.append({
                        "id": str(item.get("id") or f"rentcast-{len(candidates)}"),
                        "country": "US",
                        "city": item.get("city") or city,
                        "price": float(price),
                        "currency": "USD",
                        "price_per_sqm": price_per_sqm,
                        "gross_yield": None,
                        "url": item.get("url") or item.get("listing_url"),
                        "source": "rentcast",
                        "score": score,
                        "raw": item,
                    })

    # ── Apify Global Property Search (non-US) ─────────────────────────────────
    if APIFY_TOKEN and search.countries:
        actor_id = (
            APIFY_GLOBAL_PROPERTY_SEARCH_ACTOR_ID
            or "wonderful_beluga~global-property-search"
        )
        async with httpx.AsyncClient(timeout=120) as client:
            for country_code in search.countries[:3]:
                if country_code.upper() in {"US", "USA", "UNITED STATES"}:
                    continue
                city = search.cities[0] if search.cities else None
                apify_input = {
                    "country": country_code.lower(),
                    "city": city or "",
                    "targetSite": "auto",
                    "category": "sale",
                    "propertyType": "all",
                    "minPrice": int(search.budget_min),
                    "maxPrice": int(search.budget_max),
                }
                run_url = (
                    f"https://api.apify.com/v2/acts/{actor_id}/runs"
                    f"?token={APIFY_TOKEN}&waitForFinish=120&timeout=120000"
                )
                try:
                    run_res = await client.post(run_url, json=apify_input)
                    run_res.raise_for_status()
                    run_data = run_res.json()
                except Exception as exc:
                    print(f"Apify run error for {country_code}: {exc}")
                    continue

                dataset_id = (run_data.get("data") or {}).get("defaultDatasetId")
                if not dataset_id:
                    continue

                items_url = (
                    f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                    f"?token={APIFY_TOKEN}&clean=true&format=json"
                )
                try:
                    items_res = await client.get(items_url)
                    items_res.raise_for_status()
                    items = items_res.json()
                except Exception as exc:
                    print(f"Apify dataset error for {country_code}: {exc}")
                    continue

                if not isinstance(items, list):
                    continue

                for item in items:
                    price = item.get("price") or item.get("priceValue")
                    if price is None:
                        continue
                    try:
                        price_val = float(price)
                    except Exception:
                        continue
                    if not (search.budget_min <= price_val <= search.budget_max):
                        continue

                    size = item.get("size") or item.get("area")
                    price_per_sqm = None
                    if size:
                        try:
                            sqm = float(size)
                            if sqm > 0:
                                price_per_sqm = price_val / sqm
                        except Exception:
                            pass

                    center = (search.budget_min + search.budget_max) / 2
                    span = max(search.budget_max - search.budget_min, 1.0)
                    distance = abs(price_val - center) / span
                    score = max(0.0, 100.0 - distance * 40.0)

                    candidates.append({
                        "id": str(item.get("id") or f"apify-{len(candidates)}"),
                        "country": item.get("countryCode") or country_code.upper(),
                        "city": item.get("city") or item.get("location") or city,
                        "price": price_val,
                        "currency": item.get("currency") or item.get("currencyCode"),
                        "price_per_sqm": price_per_sqm,
                        "gross_yield": None,
                        "url": item.get("url") or item.get("detailUrl"),
                        "source": "apify_global_property_search",
                        "score": score,
                        "raw": item,
                    })

    candidates.sort(key=lambda x: (x.get("score") or 0.0), reverse=True)
    return candidates


# ─── Misc helpers ─────────────────────────────────────────────────────────────

def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_email_verified=user.is_email_verified,
        plan=user.plan,
        free_credits=user.free_credits,
        paid_credits=user.paid_credits,
        total_credits=total_credits(user),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        user_id = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_stripe_price_id(plan: str) -> str:
    if plan == "starter" and STRIPE_PRICE_STARTER:
        return STRIPE_PRICE_STARTER
    if plan == "pro" and STRIPE_PRICE_PRO:
        return STRIPE_PRICE_PRO
    raise ValueError("Stripe price not configured for this plan")


def plan_from_price_id(price_id: Optional[str]) -> str:
    if price_id == STRIPE_PRICE_STARTER:
        return "starter"
    if price_id == STRIPE_PRICE_PRO:
        return "pro"
    return "free"


# ─── Demo Data ────────────────────────────────────────────────────────────────

DEMO_PROPERTIES = [
    {
        "id": 1,
        "title": "Luxury 6BR Villa with Private Beach - Palm Jumeirah",
        "price": 18500000, "currency": "AED", "area": 750,
        "city": "Dubai", "country": "UAE", "bedrooms": 6, "bathrooms": 7,
        "property_type": "villa",
        "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800",
        "location": "Palm Jumeirah",
        "description": "Exclusive beachfront villa with private pool."
    },
    {
        "id": 2,
        "title": "2BR Luxury Apartment - Burj Khalifa View",
        "price": 2350000, "currency": "AED", "area": 145,
        "city": "Dubai", "country": "UAE", "bedrooms": 2, "bathrooms": 2,
        "property_type": "apartment",
        "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800",
        "location": "Downtown Dubai",
        "description": "Stunning apartment with direct Burj Khalifa views."
    },
    {
        "id": 3,
        "title": "4BR Townhouse - Arabian Ranches 3",
        "price": 2850000, "currency": "AED", "area": 320,
        "city": "Dubai", "country": "UAE", "bedrooms": 4, "bathrooms": 4,
        "property_type": "townhouse",
        "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800",
        "location": "Arabian Ranches 3",
        "description": "Modern townhouse in family-friendly community."
    },
    {
        "id": 4,
        "title": "1BR Sea View Apartment - Marina Towers",
        "price": 1450000, "currency": "AED", "area": 95,
        "city": "Dubai", "country": "UAE", "bedrooms": 1, "bathrooms": 1,
        "property_type": "apartment",
        "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800",
        "location": "Dubai Marina",
        "description": "Bright apartment with stunning sea and marina views."
    },
    {
        "id": 5,
        "title": "3BR Duplex Penthouse - Business Bay",
        "price": 4200000, "currency": "AED", "area": 350,
        "city": "Dubai", "country": "UAE", "bedrooms": 3, "bathrooms": 4,
        "property_type": "penthouse",
        "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800",
        "location": "Business Bay",
        "description": "Luxury duplex penthouse with private terrace and canal views."
    },
]

UAE_AREAS = [
    {"name": "JVC", "nameAr": "قرية جميرا", "avgRentYield": 7.5,
     "avgPricePerSqFt": 1100, "medianPrice": 950000, "deal_score": 95,
     "riskLevel": "Low", "priceTrend": "rising"},
    {"name": "International City", "nameAr": "المدينة العالمية",
     "avgRentYield": 9.0, "avgPricePerSqFt": 650, "medianPrice": 550000,
     "deal_score": 93, "riskLevel": "Medium", "priceTrend": "rising"},
    {"name": "Dubai Silicon Oasis", "nameAr": "واحة دبي",
     "avgRentYield": 7.8, "avgPricePerSqFt": 850, "medianPrice": 780000,
     "deal_score": 93, "riskLevel": "Low", "priceTrend": "rising"},
    {"name": "Discovery Gardens", "nameAr": "حدائق ديسكفري",
     "avgRentYield": 8.5, "avgPricePerSqFt": 750, "medianPrice": 650000,
     "deal_score": 91, "riskLevel": "Low", "priceTrend": "stable"},
    {"name": "Dubai Land", "nameAr": "أرض دبي",
     "avgRentYield": 8.0, "avgPricePerSqFt": 700, "medianPrice": 900000,
     "deal_score": 90, "riskLevel": "Medium", "priceTrend": "rising"},
    {"name": "Dubai Marina", "nameAr": "مارينا دبي",
     "avgRentYield": 5.5, "avgPricePerSqFt": 1650, "medianPrice": 1650000,
     "deal_score": 88, "riskLevel": "Low", "priceTrend": "stable"},
    {"name": "Business Bay", "nameAr": "الخليج التجاري",
     "avgRentYield": 5.8, "avgPricePerSqFt": 1200, "medianPrice": 1200000,
     "deal_score": 85, "riskLevel": "Medium", "priceTrend": "rising"},
]


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "app": APP_NAME, "env": ENVIRONMENT}


@app.post("/auth/register", response_model=MessageOut)
async def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    email = sanitize_email(body.email)
    ip = get_client_ip(request)
    fingerprint = get_device_fingerprint(request)

    if is_disposable_email(email):
        log_signup_attempt(db, email, ip, fingerprint, False, "disposable_email")
        raise HTTPException(status_code=400, detail="Disposable emails are not allowed")

    if not can_register_from_ip(db, ip):
        log_signup_attempt(db, email, ip, fingerprint, False, "signup_rate_limited")
        raise HTTPException(status_code=429, detail="Too many signup attempts from this IP")

    if not await verify_turnstile(body.captcha_token, ip):
        log_signup_attempt(db, email, ip, fingerprint, False, "captcha_failed")
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    if db.query(User).filter(User.email == email).first():
        log_signup_attempt(db, email, ip, fingerprint, False, "email_exists")
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=email,
        password_hash=hash_password(body.password),
        is_email_verified=False,
        plan="free",
        free_credits=0,
        paid_credits=0,
        trial_eligible=is_trial_eligible(db, ip, fingerprint),
        signup_ip=ip,
        signup_fingerprint=fingerprint,
    )
    db.add(user)
    db.flush()

    raw_token = generate_token()
    token_row = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=utcnow() + timedelta(hours=24),
    )
    db.add(token_row)
    db.commit()

    send_verification_email(user.email, raw_token)
    log_signup_attempt(db, email, ip, fingerprint, True, "registered")

    return MessageOut(
        message="Registered successfully. Verify your email to activate free credits."
    )


@app.post("/auth/verify-email", response_model=TokenOut)
def verify_email(body: VerifyEmailIn, db: Session = Depends(get_db)):
    token_hash_value = hash_token(body.token)
    row = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == token_hash_value,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at >= utcnow(),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.get(User, row.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_email_verified = True
    if user.trial_eligible and not user.trial_granted:
        grant_trial_credits(user)

    row.used_at = utcnow()
    db.commit()

    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=user_to_out(user))


@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    email = sanitize_email(body.email)
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Verify your email first")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Account blocked")

    ip = get_client_ip(request)
    fingerprint = get_device_fingerprint(request)
    user.last_login_at = utcnow()
    db.add(LoginEvent(
        user_id=user.id,
        ip=ip,
        fingerprint=fingerprint,
        user_agent=request.headers.get("user-agent", ""),
    ))
    db.commit()

    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=user_to_out(user))


@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return user_to_out(current_user)


@app.post("/analysis", response_model=AnalysisOut)
async def analyze_property(
    body: PropertyAnalysisIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Account blocked")
    if not current_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    ip = get_client_ip(request)
    fingerprint = get_device_fingerprint(request)

    if is_analysis_rate_limited(db, current_user.id, ip):
        raise HTTPException(status_code=429, detail="Too many requests, slow down")

    payload_dict = payload_to_dict(body)
    normalized_url = normalize_url(payload_dict["property_url"])
    cache_key = build_cache_key(payload_dict)

    cache = (
        db.query(AnalysisCache)
        .filter(
            AnalysisCache.cache_key == cache_key,
            AnalysisCache.expires_at >= utcnow(),
        )
        .first()
    )

    if cache:
        db.add(AnalysisJob(
            user_id=current_user.id,
            property_url=body.property_url,
            normalized_url=normalized_url,
            cache_key=cache_key,
            provider_used=cache.provider_used,
            model_used=cache.model_used,
            credits_charged=0,
            credit_source=None,
            cached=True,
            raw_request=payload_dict,
            response_text=cache.response_text,
            response_json=cache.response_json,
            ip=ip,
            fingerprint=fingerprint,
        ))
        db.commit()
        return AnalysisOut(
            cached=True,
            provider=cache.provider_used,
            model=cache.model_used,
            remaining_credits=total_credits(current_user),
            credit_source=None,
            analysis=cache.response_json,
        )

    if total_credits(current_user) <= 0:
        raise HTTPException(status_code=402, detail="No credits available")

    try:
        result = await generate_analysis(payload_dict)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    credit_source = consume_one_credit(current_user)

    db.add(AnalysisCache(
        cache_key=cache_key,
        normalized_url=normalized_url,
        response_text=result["raw_text"],
        response_json=result["parsed"],
        provider_used=result["provider"],
        model_used=result["model"],
        expires_at=utcnow() + timedelta(hours=ANALYSIS_CACHE_HOURS),
    ))

    db.add(AnalysisJob(
        user_id=current_user.id,
        property_url=body.property_url,
        normalized_url=normalized_url,
        cache_key=cache_key,
        provider_used=result["provider"],
        model_used=result["model"],
        credits_charged=1,
        credit_source=credit_source,
        cached=False,
        raw_request=payload_dict,
        response_text=result["raw_text"],
        response_json=result["parsed"],
        ip=ip,
        fingerprint=fingerprint,
    ))
    db.commit()
    db.refresh(current_user)

    return AnalysisOut(
        cached=False,
        provider=result["provider"],
        model=result["model"],
        remaining_credits=total_credits(current_user),
        credit_source=credit_source,
        analysis=result["parsed"],
    )


@app.post("/search-deals", response_model=SearchDealsOut)
async def search_deals(
    body: SearchDealsIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Account blocked")
    if not current_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    ip = get_client_ip(request)
    fingerprint = get_device_fingerprint(request)

    if is_analysis_rate_limited(db, current_user.id, ip):
        raise HTTPException(status_code=429, detail="Too many requests, slow down")

    if total_credits(current_user) <= 0:
        raise HTTPException(status_code=402, detail="No credits available")

    search_params_dict = body.model_dump(exclude_none=True)
    candidates = await fetch_candidate_properties(body)

    if not candidates:
        raise HTTPException(
            status_code=502,
            detail="No candidate properties returned for these filters.",
        )

    try:
        llm_result = await generate_deals_summary(search_params_dict, candidates)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        credit_source = consume_one_credit(current_user)
    except ValueError:
        raise HTTPException(status_code=402, detail="No credits available")

    ai_summary = llm_result["parsed"]

    db.add(DealsSearchJob(
        user_id=current_user.id,
        search_params=search_params_dict,
        candidates=candidates,
        ai_summary=ai_summary,
        provider_used=llm_result["provider"],
        model_used=llm_result["model"],
        credits_charged=1,
        credit_source=credit_source,
        ip=ip,
        fingerprint=fingerprint,
    ))
    db.commit()
    db.refresh(current_user)

    deals_out = [
        DealCandidateOut(
            id=str(c.get("id") or ""),
            country=c.get("country"),
            city=c.get("city"),
            price=c.get("price"),
            currency=c.get("currency"),
            price_per_sqm=c.get("price_per_sqm"),
            gross_yield=c.get("gross_yield"),
            url=c.get("url"),
            source=c.get("source"),
            score=c.get("score"),
            raw=c,
        )
        for c in candidates[: body.limit]
    ]

    return SearchDealsOut(
        provider=llm_result["provider"],
        model=llm_result["model"],
        remaining_credits=total_credits(current_user),
        credit_source=credit_source,
        search_params=search_params_dict,
        ai_summary=ai_summary,
        deals=deals_out,
    )


@app.post("/billing/checkout", response_model=CheckoutOut)
def billing_checkout(
    body: CheckoutIn,
    current_user: User = Depends(get_current_user),
):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe is not configured")

    plan = body.plan.strip().lower()
    if plan not in {"starter", "pro"}:
        raise HTTPException(status_code=400, detail="Allowed plans: starter, pro")

    try:
        price_id = get_stripe_price_id(plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": (
            f"{FRONTEND_URL.rstrip('/')}/billing/success"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        "cancel_url": f"{FRONTEND_URL.rstrip('/')}/pricing",
        "metadata": {"user_id": current_user.id, "plan": plan},
    }

    if current_user.stripe_customer_id:
        params["customer"] = current_user.stripe_customer_id
    else:
        params["customer_email"] = current_user.email

    session = stripe.checkout.Session.create(**params)
    return CheckoutOut(checkout_url=session.url)


@app.post("/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Stripe is not configured")

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = (obj.get("metadata") or {}).get("user_id")
        if user_id:
            user = db.get(User, user_id)
            if user:
                user.stripe_customer_id = obj.get("customer")
                db.commit()

    elif event_type == "invoice.paid":
        customer_id = obj.get("customer")
        if customer_id:
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                price_id = None
                for line in obj.get("lines", {}).get("data", []):
                    price = line.get("price") or {}
                    if price.get("id"):
                        price_id = price["id"]
                        break
                plan = plan_from_price_id(price_id)
                refill_plan_credits(user, plan)
                user.stripe_subscription_id = obj.get("subscription")
                db.commit()

    elif event_type == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        if customer_id:
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                refill_plan_credits(user, "free")
                user.stripe_subscription_id = None
                db.commit()

    return {"received": True}



