from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="AI Real Estate Deals Finder",
    version="2.0.0",
    description="AI-powered real estate deal finder"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Real Estate Deals Finder API",
        "version": "2.0.0",
        "docs": "/docs"
    }


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/v1/auth/login")
def login(request: LoginRequest):
    if request.email == "test@demo.com" and request.password == "demo123":
        return {"access_token": "demo-access-token", "token_type": "bearer"}
    return {"error": "Invalid credentials"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
