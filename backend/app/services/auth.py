from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2Scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Demo user bypass
        if user_id_str == "demo":
            # Create or get demo user
            demo_user = db.query(User).filter(User.email == "test@demo.com").first()
            if not demo_user:
                demo_user = User(
                    email="test@demo.com",
                    full_name="Demo User",
                    hashed_password=get_password_hash("demo123"),
                    is_active=True,
                    referral_code="DEMO2024",
                    credits=10
                )
                db.add(demo_user)
                db.commit()
                db.refresh(demo_user)
            return demo_user
            
        user_id = int(user_id_str)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def generate_referral_code() -> str:
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def use_credit(db: Session, user: User, amount: int = 1) -> bool:
    """Deduct credits from user account"""
    if user.credits < amount:
        return False
    user.credits -= amount
    db.commit()
    return True


def add_credits(db: Session, user: User, amount: int) -> None:
    """Add credits to user account"""
    user.credits += amount
    db.commit()
