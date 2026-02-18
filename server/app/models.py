from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    picture = Column(String)
    delta_api_key = Column(String, nullable=True)
    delta_api_secret = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    strategies = relationship("Strategy", back_populates="owner")

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    symbol = Column(String)
    broker = Column(String)
    logic_configuration = Column(JSON)
    is_running = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="strategies")
    # Link to logs
    logs = relationship("StrategyLog", back_populates="strategy", cascade="all, delete-orphan")

# NEW TABLE FOR LOGS
class StrategyLog(Base):
    __tablename__ = "strategy_logs"
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    message = Column(Text)
    level = Column(String) # INFO, ERROR, SUCCESS, WARNING
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="logs")
