# server/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# We use SQLite for local dev (fast), Postgres for Prod (scalable)
SQLALCHEMY_DATABASE_URL = "sqlite:///./algotrade.db"

# "check_same_thread": False is needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session in API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()