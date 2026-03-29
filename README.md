# AI Real Estate Deals Finder

An AI-powered SaaS application that helps users find undervalued real estate properties in the UAE, specifically Dubai.

## Features

- **Property Listings**: Browse properties from Dubai, Abu Dhabi, and Sharjah
- **AI Deal Scoring**: Properties rated 0-100 based on price vs market average
- **Best Deals**: AI-curated list of undervalued properties
- **Interactive Map**: OpenStreetMap-based property visualization
- **Credit System**: 3 free analyses for new users, then pay-as-you-go
- **Stripe Payments**: Purchase credits via Stripe
- **Referral System**: Earn credits by inviting friends

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Auth**: JWT tokens
- **Payments**: Stripe

### Frontend
- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **Maps**: OpenStreetMap with Leaflet
- **State**: Zustand
- **API Client**: Axios

## Project Structure

```
ai-real-estate-finder/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic (auth, deal scorer)
│   │   ├── config.py      # Settings
│   │   ├── database.py    # DB connection
│   │   └── main.py        # FastAPI app
│   ├── alembic/           # Database migrations
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/               # Next.js app directory
│   │   ├── page.tsx       # Home page
│   │   ├── best-deals/    # Best deals page
│   │   ├── analyze/       # Analysis form
│   │   ├── dashboard/     # User dashboard
│   │   ├── login/         # Login page
│   │   └── register/      # Register page
│   ├── components/        # React components
│   ├── lib/               # Utilities (API, types, store)
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Stripe account (for payments)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd ai-real-estate-finder/backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL**:
   ```bash
   # Create database
   psql -U postgres
   CREATE DATABASE real_estate_db;
   \q
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database URL and secrets
   ```

6. **Run database migrations**:
   ```bash
   # Apply migrations
   alembic upgrade head
   ```

7. **Seed sample data**:
   ```bash
   python -m app.seed_data
   ```

8. **Start the server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd ai-real-estate-finder/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**: http://localhost:3000

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user

### Properties
- `GET /api/v1/properties` - List all properties
- `GET /api/v1/properties/best-deals` - Get top deals
- `GET /api/v1/properties/{id}` - Get single property
- `GET /api/v1/properties/{id}/analyze` - Analyze property

### Analysis
- `POST /api/v1/analyze` - Create new analysis
- `GET /api/v1/analyze/history` - Get analysis history
- `GET /api/v1/analyze/stats` - Get dashboard stats

### Payments
- `GET /api/v1/payments/packages` - Get credit packages
- `POST /api/v1/payments/create-checkout` - Create Stripe checkout
- `POST /api/v1/payments/webhook` - Stripe webhook handler

## Deployment

### Backend - Railway

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Add PostgreSQL database
4. Set environment variables
5. Deploy

### Frontend - Vercel

1. Create account at [vercel.com](https://vercel.com)
2. Import project from GitHub
3. Set environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

## Demo Credentials

- **Email**: demo@example.com
- **Password**: demo123

## How the AI Scoring Works

1. Calculate price per square meter for each property
2. Compare against area average (city + district)
3. Calculate percentage difference from market average
4. Apply bonuses for value factors (bedrooms per sqm)
5. Output score 0-100 with recommendation

## Market Strategy

- **UAE**: Full listings + monetization (affiliate + leads)
- **USA**: Analysis only (no scraping protected data)
- **Europe**: Limited analysis

## 30-Day MVP Checklist

- [x] Backend API with FastAPI
- [x] PostgreSQL database with models
- [x] User authentication (JWT)
- [x] Property CRUD and listing
- [x] AI deal scoring algorithm
- [x] Interactive map with Leaflet
- [x] Frontend with Next.js
- [x] Credit system
- [x] Stripe integration
- [x] Referral system
- [ ] Data scraper for real listings
- [ ] Email notifications
- [ ] Admin dashboard
- [ ] Mobile app

## License

MIT License
