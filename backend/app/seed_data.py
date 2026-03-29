"""
Seed script to populate the database with sample UAE property data.
Run with: python -m app.seed_data
"""
import sys
sys.path.insert(0, ".")

from app.database import SessionLocal, engine, Base
from app.models.models import Property, MarketStats
from app.models.models import User
from app.services.auth import get_password_hash


SAMPLE_PROPERTIES = [
    # Dubai Marina Properties
    {
        "title": "Stunning 2BR Marina View Apartment",
        "description": "Modern apartment with panoramic Marina views",
        "price": 1850000,
        "area": 145,
        "location": "Dubai Marina",
        "address": "Marina Gate Tower 2",
        "city": "Dubai",
        "district": "Dubai Marina",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "latitude": 25.0805,
        "longitude": 55.1403,
        "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800",
        "source": "mock",
    },
    {
        "title": "Luxury 3BR Penthouse with Private Pool",
        "description": "Exclusive penthouse with private rooftop pool",
        "price": 8500000,
        "area": 320,
        "location": "Dubai Marina",
        "address": "Princess Tower",
        "city": "Dubai",
        "district": "Dubai Marina",
        "country": "UAE",
        "property_type": "penthouse",
        "bedrooms": 3,
        "bathrooms": 4,
        "latitude": 25.0855,
        "longitude": 55.1443,
        "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800",
        "source": "mock",
    },
    {
        "title": "Affordable Studio Near Metro",
        "description": "Compact studio perfect for investors",
        "price": 650000,
        "area": 45,
        "location": "Dubai Marina",
        "address": "Marina Promenade",
        "city": "Dubai",
        "district": "Dubai Marina",
        "country": "UAE",
        "property_type": "studio",
        "bedrooms": 0,
        "bathrooms": 1,
        "latitude": 25.0785,
        "longitude": 55.1383,
        "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
        "source": "mock",
    },
    # Downtown Dubai Properties
    {
        "title": "Breathtaking Burj Khalifa View 2BR",
        "description": "Premium apartment with direct Burj Khalifa views",
        "price": 3200000,
        "area": 165,
        "location": "Downtown Dubai",
        "address": "Address Downtown",
        "city": "Dubai",
        "district": "Downtown Dubai",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 3,
        "latitude": 25.1972,
        "longitude": 55.2744,
        "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800",
        "source": "mock",
    },
    {
        "title": "Undervalued 1BR Near Boulevard",
        "description": "Great location, below market price",
        "price": 1150000,
        "area": 85,
        "location": "Downtown Dubai",
        "address": "Makani Heights",
        "city": "Dubai",
        "district": "Downtown Dubai",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 1,
        "bathrooms": 1,
        "latitude": 25.1895,
        "longitude": 55.2794,
        "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
        "source": "mock",
    },
    # JBR Properties
    {
        "title": "Beachfront 3BR in JBR",
        "description": "Direct beach access, premium finishes",
        "price": 4500000,
        "area": 220,
        "location": "JBR",
        "address": "Murjan 5, JBR",
        "city": "Dubai",
        "district": "JBR",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 3,
        "bathrooms": 4,
        "latitude": 25.0768,
        "longitude": 55.1316,
        "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800",
        "source": "mock",
    },
    {
        "title": "Great Value 2BR JBR Investment",
        "description": "Below market rate, high rental yield",
        "price": 1550000,
        "area": 130,
        "location": "JBR",
        "address": "Amwaj 3",
        "city": "Dubai",
        "district": "JBR",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "latitude": 25.0748,
        "longitude": 55.1346,
        "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800",
        "source": "mock",
    },
    # Palm Jumeirah Properties
    {
        "title": "Exclusive Palm Villa with Private Beach",
        "description": "Full Palm frond villa, premium location",
        "price": 25000000,
        "area": 850,
        "location": "Palm Jumeirah",
        "address": "Frond C, Palm Jumeirah",
        "city": "Dubai",
        "district": "Palm Jumeirah",
        "country": "UAE",
        "property_type": "villa",
        "bedrooms": 5,
        "bathrooms": 6,
        "latitude": 25.1124,
        "longitude": 55.1390,
        "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800",
        "source": "mock",
    },
    {
        "title": "Underpriced Palm Apartment",
        "description": "Great deal on Palm, motivated seller",
        "price": 2800000,
        "area": 180,
        "location": "Palm Jumeirah",
        "address": "Tiara United Tower",
        "city": "Dubai",
        "district": "Palm Jumeirah",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 3,
        "latitude": 25.1084,
        "longitude": 55.1410,
        "image_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=800",
        "source": "mock",
    },
    # Business Bay Properties
    {
        "title": "Modern 1BR Business Bay",
        "description": "City views, great for professionals",
        "price": 950000,
        "area": 75,
        "location": "Business Bay",
        "address": "Executive Tower H",
        "city": "Dubai",
        "district": "Business Bay",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 1,
        "bathrooms": 1,
        "latitude": 25.1865,
        "longitude": 55.2605,
        "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800",
        "source": "mock",
    },
    {
        "title": "Spacious 3BR Family Home Business Bay",
        "description": "Rare 3BR in Business Bay, family friendly",
        "price": 2200000,
        "area": 195,
        "location": "Business Bay",
        "address": "Damac Prive",
        "city": "Dubai",
        "district": "Business Bay",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "latitude": 25.1845,
        "longitude": 55.2585,
        "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800",
        "source": "mock",
    },
    # JVC Properties
    {
        "title": "Budget-Friendly 1BR JVC",
        "description": "Perfect starter home, excellent value",
        "price": 720000,
        "area": 65,
        "location": "JVC",
        "address": "Golden Mile Galleria",
        "city": "Dubai",
        "district": "JVC",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 1,
        "bathrooms": 1,
        "latitude": 25.0455,
        "longitude": 55.1955,
        "image_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800",
        "source": "mock",
    },
    {
        "title": "Undervalued 2BR Villa JVC",
        "description": "Standalone villa, huge potential",
        "price": 1850000,
        "area": 220,
        "location": "JVC",
        "address": "Circle 5",
        "city": "Dubai",
        "district": "JVC",
        "country": "UAE",
        "property_type": "villa",
        "bedrooms": 2,
        "bathrooms": 3,
        "latitude": 25.0485,
        "longitude": 55.1985,
        "image_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=800",
        "source": "mock",
    },
    # Abu Dhabi Properties
    {
        "title": "Luxury Al Reem Island 2BR",
        "description": "Premium finishes, great community",
        "price": 1350000,
        "area": 120,
        "location": "Al Reem Island",
        "address": "Gate Towers",
        "city": "Abu Dhabi",
        "district": "Al Reem Island",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "latitude": 24.4535,
        "longitude": 54.3915,
        "image_url": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800",
        "source": "mock",
    },
    {
        "title": "Yas Island Investment Property",
        "description": "High rental demand area, tourist hotspot",
        "price": 1680000,
        "area": 140,
        "location": "Yas Island",
        "address": "Yas Acres",
        "city": "Abu Dhabi",
        "district": "Yas Island",
        "country": "UAE",
        "property_type": "villa",
        "bedrooms": 3,
        "bathrooms": 4,
        "latitude": 24.4635,
        "longitude": 54.6015,
        "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800",
        "source": "mock",
    },
    # Sharjah Properties
    {
        "title": "Affordable 2BR Al Majaz",
        "description": "Prime location, family-friendly area",
        "price": 580000,
        "area": 95,
        "location": "Al Majaz",
        "address": "Al Majaz 2",
        "city": "Sharjah",
        "district": "Al Majaz",
        "country": "UAE",
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "latitude": 25.3465,
        "longitude": 55.3845,
        "image_url": "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=800",
        "source": "mock",
    },
]


def seed_properties():
    """Seed the database with sample properties"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if properties already exist
        existing = db.query(Property).count()
        if existing > 0:
            print(f"Database already has {existing} properties. Skipping seed.")
            return
        
        # Create demo user
        demo_user = User(
            email="demo@example.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            credits=10,
            referral_code="DEMO1234"
        )
        db.add(demo_user)
        
        # Add properties
        for prop_data in SAMPLE_PROPERTIES:
            price_per_m2 = prop_data["price"] / prop_data["area"] if prop_data["area"] > 0 else 0
            prop = Property(**prop_data, price_per_m2=price_per_m2)
            db.add(prop)
        
        db.commit()
        
        # Calculate and save market stats
        districts = db.query(Property.district, Property.city, Property.country, Property.property_type).distinct().all()
        for district, city, country, prop_type in districts:
            props = db.query(Property).filter(
                Property.district == district,
                Property.city == city
            ).all()
            
            if props:
                avg_price = sum(p.price_per_m2 for p in props) / len(props)
                stats = MarketStats(
                    city=city,
                    country=country,
                    district=district,
                    property_type=prop_type,
                    avg_price_per_m2=avg_price,
                    median_price_per_m2=sorted([p.price_per_m2 for p in props])[len(props)//2],
                    total_properties=len(props)
                )
                db.add(stats)
        
        db.commit()
        print(f"Successfully seeded {len(SAMPLE_PROPERTIES)} properties and market stats!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_properties()
