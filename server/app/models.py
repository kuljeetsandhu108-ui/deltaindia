# server/app/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    picture = Column(String) # Google Profile Pic
    
    # Encrypted Broker Credentials (Delta Exchange / CoinDCX)
    delta_api_key = Column(String, nullable=True)
    delta_api_secret = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategies = relationship("Strategy", back_populates="owner")

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    symbol = Column(String) # e.g. "BTCUSD"
    broker = Column(String) # "DELTA" or "COINDCX"
    
    # The "No-Code" Logic stored as JSON
    # Example: {"conditions": [{"indicator": "EMA", "period": 20...}]}
    logic_configuration = Column(JSON) 
    
    is_running = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="strategies")