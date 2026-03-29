from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to AI Real Estate Deals Finder API", "version": "2.0.0", "docs": "/docs"}


@app.post("/api/v1/auth/login")
def login(request: dict):
    email = request.get("email", "")
    password = request.get("password", "")
    if email == "test@demo.com" and password == "demo123":
        return {"access_token": "demo-access-token", "token_type": "bearer"}
    return {"error": "Invalid credentials"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/test")
def test():
    return {"result": "API is working"}


@app.get("/api/v1/auth/me")
def get_me():
    return {"id": 1, "email": "test@demo.com", "full_name": "Demo User", "credits": 100, "plan": "free"}
