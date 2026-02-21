from pydantic import BaseModel
from typing import Optional, Dict, Any

class UserCreate(BaseModel):
    email: str
    full_name: str
    picture: Optional[str] = None

class BrokerKeys(BaseModel):
    email: str
    broker: str 
    api_key: str
    api_secret: str

class StrategyInput(BaseModel):
    email: str
    name: str
    symbol: str
    broker: str = "DELTA"
    logic: Dict[str, Any]
