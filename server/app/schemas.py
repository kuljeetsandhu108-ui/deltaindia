from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    full_name: str
    picture: Optional[str] = None

class BrokerKeys(BaseModel):
    email: str # We identify user by email for simplicity in MVP
    broker: str # "DELTA" or "COINDCX"
    api_key: str
    api_secret: str

class StrategyInput(BaseModel):
    email: str
    name: str
    symbol: str
    logic: dict
