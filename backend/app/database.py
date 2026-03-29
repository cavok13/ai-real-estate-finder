from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from app.config import settings

db_path = settings.DATABASE_URL.replace("sqlite:///", "")
os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create tables
from app.models.models import Base as ModelBase
ModelBase.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
