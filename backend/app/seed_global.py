"""
Seed script with properties from around the world
"""
import sys
sys.path.insert(0, ".")

from app.database import SessionLocal, engine, Base
from app.models.models import Property, MarketStats, User
from app.services.auth import get_password_hash

GLOBAL_PROPERTIES = [
    # ============ USA ============
    {"title": "Modern Downtown Manhattan Apartment", "price": 1250000, "area": 95, "city": "New York", "country": "USA", "district": "Manhattan", "state": "NY", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": 40.7128, "longitude": -74.0060, "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"},
    {"title": "Spacious LA Family Home", "price": 950000, "area": 185, "city": "Los Angeles", "country": "USA", "district": "Beverly Hills", "state": "CA", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "house", "bedrooms": 4, "bathrooms": 3, "latitude": 34.0522, "longitude": -118.2437, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    {"title": "Miami Beach Condo", "price": 680000, "area": 85, "city": "Miami", "country": "USA", "district": "Miami Beach", "state": "FL", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "condo", "bedrooms": 2, "bathrooms": 2, "latitude": 25.7617, "longitude": -80.1918, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Austin Tech Hub Apartment", "price": 520000, "area": 75, "city": "Austin", "country": "USA", "district": "Downtown", "state": "TX", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 1, "bathrooms": 1, "latitude": 30.2672, "longitude": -97.7431, "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"},
    {"title": "Seattle Lake View Condo", "price": 750000, "area": 90, "city": "Seattle", "country": "USA", "district": "Bellevue", "state": "WA", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "condo", "bedrooms": 2, "bathrooms": 2, "latitude": 47.6062, "longitude": -122.3321, "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800"},
    {"title": "Chicago Lincoln Park Flat", "price": 485000, "area": 100, "city": "Chicago", "country": "USA", "district": "Lincoln Park", "state": "IL", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 41.9211, "longitude": -87.6513, "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800"},
    {"title": "San Francisco Mission District Loft", "price": 1100000, "area": 80, "city": "San Francisco", "country": "USA", "district": "Mission", "state": "CA", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "loft", "bedrooms": 1, "bathrooms": 1, "latitude": 37.7749, "longitude": -122.4194, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    {"title": "Boston Back Bay Brownstone", "price": 1850000, "area": 200, "city": "Boston", "country": "USA", "district": "Back Bay", "state": "MA", "region": "North America", "currency": "USD", "currency_symbol": "$", "property_type": "townhouse", "bedrooms": 4, "bathrooms": 3, "latitude": 42.3601, "longitude": -71.0589, "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800"},
    
    # ============ UK ============
    {"title": "London Canary Wharf Flat", "price": 650000, "area": 65, "city": "London", "country": "UK", "district": "Canary Wharf", "state": "England", "region": "Europe", "currency": "GBP", "currency_symbol": "£", "property_type": "flat", "bedrooms": 2, "bathrooms": 1, "latitude": 51.5045, "longitude": -0.0235, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Manchester City Centre Apartment", "price": 285000, "area": 70, "city": "Manchester", "country": "UK", "district": "City Centre", "state": "England", "region": "Europe", "currency": "GBP", "currency_symbol": "£", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 53.4808, "longitude": -2.2426, "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"},
    {"title": "Edinburgh Georgian Flat", "price": 425000, "area": 85, "city": "Edinburgh", "country": "UK", "district": "New Town", "state": "Scotland", "region": "Europe", "currency": "GBP", "currency_symbol": "£", "property_type": "flat", "bedrooms": 3, "bathrooms": 1, "latitude": 55.9533, "longitude": -3.1883, "image_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800"},
    {"title": "Birmingham Jewellery Quarter Flat", "price": 195000, "area": 60, "city": "Birmingham", "country": "UK", "district": "Jewellery Quarter", "state": "England", "region": "Europe", "currency": "GBP", "currency_symbol": "£", "property_type": "apartment", "bedrooms": 1, "bathrooms": 1, "latitude": 52.4862, "longitude": -1.8904, "image_url": "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87?w=800"},
    {"title": "Bristol Harbourside Apartment", "price": 320000, "area": 75, "city": "Bristol", "country": "UK", "district": "Harbourside", "state": "England", "region": "Europe", "currency": "GBP", "currency_symbol": "£", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 51.4545, "longitude": -2.5879, "image_url": "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=800"},
    
    # ============ Canada ============
    {"title": "Toronto Downtown Condo", "price": 720000, "area": 80, "city": "Toronto", "country": "Canada", "district": "Downtown", "state": "Ontario", "region": "North America", "currency": "CAD", "currency_symbol": "C$", "property_type": "condo", "bedrooms": 2, "bathrooms": 1, "latitude": 43.6532, "longitude": -79.3832, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    {"title": "Vancouver Yaletown Loft", "price": 950000, "area": 95, "city": "Vancouver", "country": "Canada", "district": "Yaletown", "state": "BC", "region": "North America", "currency": "CAD", "currency_symbol": "C$", "property_type": "loft", "bedrooms": 2, "bathrooms": 2, "latitude": 49.2827, "longitude": -123.1207, "image_url": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800"},
    {"title": "Montreal Plateau Apartment", "price": 385000, "area": 70, "city": "Montreal", "country": "Canada", "district": "Plateau", "state": "Quebec", "region": "North America", "currency": "CAD", "currency_symbol": "C$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 45.5017, "longitude": -73.5673, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    {"title": "Calgary Beltline Condo", "price": 320000, "area": 75, "city": "Calgary", "country": "Canada", "district": "Beltline", "state": "Alberta", "region": "North America", "currency": "CAD", "currency_symbol": "C$", "property_type": "condo", "bedrooms": 1, "bathrooms": 1, "latitude": 51.0447, "longitude": -114.0719, "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800"},
    
    # ============ Germany ============
    {"title": "Berlin Mitte Apartment", "price": 485000, "area": 75, "city": "Berlin", "country": "Germany", "district": "Mitte", "state": "Berlin", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 52.5200, "longitude": 13.4050, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Munich Schwabing Flat", "price": 750000, "area": 85, "city": "Munich", "country": "Germany", "district": "Schwabing", "state": "Bavaria", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 3, "bathrooms": 1, "latitude": 48.1351, "longitude": 11.5820, "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800"},
    {"title": "Hamburg Eppendorf Apartment", "price": 520000, "area": 80, "city": "Hamburg", "country": "Germany", "district": "Eppendorf", "state": "Hamburg", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 53.5488, "longitude": 9.9872, "image_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800"},
    {"title": "Frankfurt Westend Flat", "price": 580000, "area": 70, "city": "Frankfurt", "country": "Germany", "district": "Westend", "state": "Hesse", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 50.1109, "longitude": 8.6821, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    
    # ============ France ============
    {"title": "Paris Marais Apartment", "price": 680000, "area": 65, "city": "Paris", "country": "France", "district": "Le Marais", "state": "Ile-de-France", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 48.8566, "longitude": 2.3522, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Lyon Presqu'ile Flat", "price": 320000, "area": 75, "city": "Lyon", "country": "France", "district": "Presqu'ile", "state": "Auvergne-Rhône-Alpes", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 45.7640, "longitude": 4.8357, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    {"title": "Nice Promenade Flat", "price": 425000, "area": 70, "city": "Nice", "country": "France", "district": "Promenade", "state": "Provence-Alpes-Côte d'Azur", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 43.7102, "longitude": 7.2620, "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800"},
    {"title": "Marseille Vieux-Port Apartment", "price": 245000, "area": 65, "city": "Marseille", "country": "France", "district": "Vieux-Port", "state": "Provence-Alpes-Côte d'Azur", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 1, "bathrooms": 1, "latitude": 43.2965, "longitude": 5.3698, "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800"},
    
    # ============ Spain ============
    {"title": "Barcelona Eixample Apartment", "price": 380000, "area": 80, "city": "Barcelona", "country": "Spain", "district": "Eixample", "state": "Catalonia", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 3, "bathrooms": 1, "latitude": 41.3851, "longitude": 2.1734, "image_url": "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=800"},
    {"title": "Madrid Salamanca Flat", "price": 520000, "area": 90, "city": "Madrid", "country": "Spain", "district": "Salamanca", "state": "Community of Madrid", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 3, "bathrooms": 2, "latitude": 40.4168, "longitude": -3.7038, "image_url": "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87?w=800"},
    {"title": "Malaga Centro Apartment", "price": 195000, "area": 70, "city": "Malaga", "country": "Spain", "district": "Centro", "state": "Andalusia", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 36.7213, "longitude": -4.4214, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    {"title": "Valencia Ruzafa Apartment", "price": 165000, "area": 75, "city": "Valencia", "country": "Spain", "district": "Ruzafa", "state": "Valencia", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 39.4699, "longitude": -0.3763, "image_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800"},
    
    # ============ Netherlands ============
    {"title": "Amsterdam Canal Apartment", "price": 580000, "area": 75, "city": "Amsterdam", "country": "Netherlands", "district": "Jordaan", "state": "North Holland", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 52.3676, "longitude": 4.9041, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Rotterdam City Centre Flat", "price": 285000, "area": 70, "city": "Rotterdam", "country": "Netherlands", "district": "City Centre", "state": "South Holland", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 51.9244, "longitude": 4.4777, "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800"},
    {"title": "The Hague Scheveningen Apartment", "price": 325000, "area": 80, "city": "The Hague", "country": "Netherlands", "district": "Scheveningen", "state": "South Holland", "region": "Europe", "currency": "EUR", "currency_symbol": "€", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 52.0705, "longitude": 4.2983, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    
    # ============ Asia ============
    {"title": "Tokyo Shibuya Modern Apartment", "price": 450000, "area": 55, "city": "Tokyo", "country": "Japan", "district": "Shibuya", "state": "Tokyo", "region": "Asia", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 1, "bathrooms": 1, "latitude": 35.6762, "longitude": 139.6503, "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800"},
    {"title": "Singapore Marina Bay Condo", "price": 1200000, "area": 100, "city": "Singapore", "country": "Singapore", "district": "Marina Bay", "state": "Central Region", "region": "Asia", "currency": "USD", "currency_symbol": "$", "property_type": "condo", "bedrooms": 3, "bathrooms": 2, "latitude": 1.2838, "longitude": 103.8591, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Hong Kong Central Apartment", "price": 1850000, "area": 70, "city": "Hong Kong", "country": "China", "district": "Central", "state": "Hong Kong Island", "region": "Asia", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": 22.2855, "longitude": 114.1577, "image_url": "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87?w=800"},
    {"title": "Seoul Gangnam Apartment", "price": 680000, "area": 85, "city": "Seoul", "country": "South Korea", "district": "Gangnam", "state": "Seoul", "region": "Asia", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 3, "bathrooms": 2, "latitude": 37.5665, "longitude": 126.9780, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    {"title": "Mumbai Bandra West Flat", "price": 520000, "area": 90, "city": "Mumbai", "country": "India", "district": "Bandra West", "state": "Maharashtra", "region": "Asia", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": 19.0596, "longitude": 72.8295, "image_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800"},
    {"title": "Bangkok Sukhumvit Condo", "price": 185000, "area": 65, "city": "Bangkok", "country": "Thailand", "district": "Sukhumvit", "state": "Bangkok", "region": "Asia", "currency": "USD", "currency_symbol": "$", "property_type": "condo", "bedrooms": 1, "bathrooms": 1, "latitude": 13.7563, "longitude": 100.5018, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    {"title": "Dubai Marina Apartment", "price": 450000, "area": 95, "city": "Dubai", "country": "UAE", "district": "Marina", "state": "Dubai", "region": "Middle East", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": 25.0805, "longitude": 55.1403, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Abu Dhabi Al Reem Island Flat", "price": 320000, "area": 85, "city": "Abu Dhabi", "country": "UAE", "district": "Al Reem Island", "state": "Abu Dhabi", "region": "Middle East", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": 24.4535, "longitude": 54.3915, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    
    # ============ Africa ============
    {"title": "Cape Town Sea Point Apartment", "price": 285000, "area": 80, "city": "Cape Town", "country": "South Africa", "district": "Sea Point", "state": "Western Cape", "region": "Africa", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": -33.9180, "longitude": 18.4233, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Johannesburg Sandton House", "price": 380000, "area": 150, "city": "Johannesburg", "country": "South Africa", "district": "Sandton", "state": "Gauteng", "region": "Africa", "currency": "USD", "currency_symbol": "$", "property_type": "house", "bedrooms": 4, "bathrooms": 3, "latitude": -26.2041, "longitude": 28.0473, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    {"title": "Nairobi Kilimani Apartment", "price": 165000, "area": 75, "city": "Nairobi", "country": "Kenya", "district": "Kilimani", "state": "Nairobi County", "region": "Africa", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": -1.2921, "longitude": 36.8219, "image_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800"},
    {"title": "Lagos Victoria Island Flat", "price": 220000, "area": 90, "city": "Lagos", "country": "Nigeria", "district": "Victoria Island", "state": "Lagos", "region": "Africa", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 3, "bathrooms": 3, "latitude": 6.5244, "longitude": 3.3792, "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800"},
    {"title": "Casablanca Maarif Apartment", "price": 195000, "area": 85, "city": "Casablanca", "country": "Morocco", "district": "Maarif", "state": "Casablanca-Settat", "region": "Africa", "currency": "USD", "currency_symbol": "$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": 33.5731, "longitude": -7.5898, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    {"title": "Cairo New Cairo Villa", "price": 450000, "area": 280, "city": "Cairo", "country": "Egypt", "district": "New Cairo", "state": "Cairo", "region": "Africa", "currency": "USD", "currency_symbol": "$", "property_type": "villa", "bedrooms": 5, "bathrooms": 4, "latitude": 30.0444, "longitude": 31.2357, "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"},
    
    # ============ Australia ============
    {"title": "Sydney CBD Apartment", "price": 720000, "area": 75, "city": "Sydney", "country": "Australia", "district": "CBD", "state": "NSW", "region": "Oceania", "currency": "AUD", "currency_symbol": "A$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": -33.8688, "longitude": 151.2093, "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"},
    {"title": "Melbourne Fitzroy Flat", "price": 485000, "area": 70, "city": "Melbourne", "country": "Australia", "district": "Fitzroy", "state": "VIC", "region": "Oceania", "currency": "AUD", "currency_symbol": "A$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 1, "latitude": -37.7964, "longitude": 144.9689, "image_url": "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87?w=800"},
    {"title": "Brisbane South Bank Condo", "price": 380000, "area": 80, "city": "Brisbane", "country": "Australia", "district": "South Bank", "state": "QLD", "region": "Oceania", "currency": "AUD", "currency_symbol": "A$", "property_type": "condo", "bedrooms": 2, "bathrooms": 2, "latitude": -27.4698, "longitude": 153.0251, "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800"},
    {"title": "Perth Subiaco Apartment", "price": 425000, "area": 85, "city": "Perth", "country": "Australia", "district": "Subiaco", "state": "WA", "region": "Oceania", "currency": "AUD", "currency_symbol": "A$", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2, "latitude": -31.9535, "longitude": 115.8030, "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800"},
]


def seed_global_properties():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        existing_countries = db.query(Property.country).distinct().all()
        existing_countries = [c[0] for c in existing_countries]
        
        new_props = 0
        for p in GLOBAL_PROPERTIES:
            if p['country'] not in existing_countries:
                price_per_m2 = p['price'] / p['area'] if p['area'] > 0 else 0
                prop = Property(
                    price_per_m2=price_per_m2,
                    **p
                )
                db.add(prop)
                new_props += 1
        
        if new_props > 0:
            db.commit()
            
            cities = db.query(Property.city, Property.country).distinct().all()
            for city, country in cities:
                props = db.query(Property).filter(
                    Property.city == city,
                    Property.country == country
                ).all()
                if props:
                    prices = [p.price_per_m2 for p in props if p.price_per_m2]
                    avg_price = sum(prices) / len(prices) if prices else 0
                    stats = MarketStats(
                        city=city,
                        country=country,
                        avg_price_per_m2=avg_price,
                        median_price_per_m2=sorted(prices)[len(prices)//2] if prices else 0,
                        total_properties=len(props),
                        currency=props[0].currency if props else "USD"
                    )
                    db.add(stats)
            
            db.commit()
            print(f"Successfully added {new_props} global properties!")
        else:
            print("Global properties already exist. Skipping.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_global_properties()
