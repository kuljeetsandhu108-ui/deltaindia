import asyncio
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
from app import models, database, schemas, crud
from app.engine import engine as trading_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(trading_engine.start())
    yield
    trading_engine.is_running = False

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="AlgoTradeIndia Engine", lifespan=lifespan)

# FIXED: ALLOW ALL ORIGINS FOR LIVE SITE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow testeralgo.online
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home(): return {"status": "System Online", "engine": "Running"}

@app.post("/auth/sync")
def sync_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user: return crud.create_user(db=db, user=user)
    return {"status": "User exists", "id": db_user.id}

@app.post("/user/keys")
def save_keys(keys: schemas.BrokerKeys, db: Session = Depends(database.get_db)):
    updated_user = crud.update_broker_keys(db, keys)
    if not updated_user:
        try:
             new_user = schemas.UserCreate(email=keys.email, full_name="Trader", picture="")
             crud.create_user(db, new_user)
             crud.update_broker_keys(db, keys)
        except: raise HTTPException(status_code=404, detail="User syncing error.")
    return {"status": "Keys Encrypted & Saved"}

@app.post("/strategy/create")
def create_strategy(strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    new_strat = crud.create_strategy(db, strat)
    if not new_strat: raise HTTPException(status_code=404, detail="User not found")
    return {"status": "Strategy Deployed", "id": new_strat.id}

@app.get("/strategies/{email}")
def get_user_strategies(email: str, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email)
    if not user: return []
    return user.strategies
