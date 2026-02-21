import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get DB URL from Docker, fallback to sqlite for local testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./algotrade.db")

if "sqlite" in DATABASE_URL:
    # Local Dev Mode
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # 🚀 ENTERPRISE POSTGRESQL MODE (For 1000+ Users)
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,         # Hold 20 open connections ready to go
        max_overflow=10,      # Allow 10 extra connections during traffic spikes
        pool_timeout=30,      # Don't panic immediately if busy, wait up to 30s
        pool_recycle=1800     # Refresh connections every 30 mins to prevent timeouts
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()
