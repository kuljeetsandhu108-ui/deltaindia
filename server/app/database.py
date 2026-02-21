import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. READ FROM ENVIRONMENT VARIABLE (Docker Sets This)
# If not found, fallback to local sqlite file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./algotrade.db")

# 2. CONFIGURE CONNECTION ARGS
# SQLite needs "check_same_thread", Postgres does NOT.
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
