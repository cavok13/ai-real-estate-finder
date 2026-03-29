from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    credits = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    referral_code = Column(String(20), unique=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Stripe fields
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100))
    subscription_status = Column(String(50), default="free")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="user")
    analyses = relationship("Analysis", back_populates="user")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    currency_symbol = Column(String(5), default="$")
    area = Column(Float, nullable=False)
    price_per_m2 = Column(Float)
    location = Column(String(255))
    address = Column(String(500))
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100))
    district = Column(String(100), index=True)
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(50), index=True)
    postal_code = Column(String(20))
    property_type = Column(String(50))
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    year_built = Column(Integer)
    parking = Column(Integer, default=0)
    latitude = Column(Float)
    longitude = Column(Float)
    image_url = Column(String(500))
    source_url = Column(String(500))
    source = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    analyses = relationship("Analysis", back_populates="property")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer)
    currency = Column(String(3), default="USD")
    price_cents = Column(Integer)
    stripe_payment_id = Column(String(255))
    stripe_session_id = Column(String(255))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    
    budget_min = Column(Float)
    budget_max = Column(Float)
    preferred_city = Column(String(100))
    preferred_country = Column(String(100))
    
    deal_score = Column(Float)
    price_vs_market = Column(Float)
    recommendation = Column(Text)
    insights = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="analyses")
    property = relationship("Property", back_populates="analyses")


class MarketStats(Base):
    __tablename__ = "market_stats"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    district = Column(String(100), index=True)
    property_type = Column(String(50))
    avg_price_per_m2 = Column(Float)
    median_price_per_m2 = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    total_properties = Column(Integer)
    currency = Column(String(3), default="USD")
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
