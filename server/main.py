import asyncio
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app import models, database, schemas, crud
from app.engine import engine as trading_engine
from app.backtester import backtester
from app.brokers.coindcx import coindcx_manager # Import New Manager
import ccxt.async_support as ccxt

# --- DUAL CACHE ---
symbol_cache = {
    "DELTA": ["BTCUSD", "ETHUSD"],
    "COINDCX": ["BTC/USDT", "ETH/USDT"]
}

async def refresh_symbols_delta():
    global symbol_cache
    try:
        exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
        markets = await exchange.load_markets()
        syms = [m['id'] for k, m in markets.items() if m.get('active') and ('USDT' in m.get('id') or 'USD' in m.get('id'))]
        if syms: symbol_cache["DELTA"] = sorted(list(set(syms)))
        await exchange.close()
    except: pass

async def refresh_symbols_coindcx():
    global symbol_cache
    syms = await coindcx_manager.fetch_symbols()
    if syms: symbol_cache["COINDCX"] = syms

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fetch both on startup
    await refresh_symbols_delta()
    await refresh_symbols_coindcx()
    asyncio.create_task(trading_engine.start())
    yield
    trading_engine.is_running = False

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="AlgoTradeIndia Engine", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home(): return {"status": "Online"}

# --- SMART ROUTER ---
@app.get("/data/symbols")
async def get_symbols(broker: str = "DELTA"):
    broker = broker.upper()
    # Lazy load if empty
    if len(symbol_cache.get(broker, [])) <= 4:
        if broker == "DELTA": await refresh_symbols_delta()
        elif broker == "COINDCX": await refresh_symbols_coindcx()
    return symbol_cache.get(broker, [])

@app.post("/auth/sync")
def sync_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user: return crud.create_user(db=db, user=user)
    return {"status": "User exists", "id": db_user.id}

@app.post("/user/keys")
def save_keys(keys: schemas.BrokerKeys, db: Session = Depends(database.get_db)):
    # Handles both brokers dynamically based on input
    crud.update_broker_keys(db, keys)
    return {"status": "Keys Saved"}

@app.post("/strategy/create")
def create_strategy(strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    new_strat = crud.create_strategy(db, strat)
    return {"status": "Deployed", "id": new_strat.id}

@app.get("/strategies/{email}")
def get_user_strategies(email: str, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email)
    return user.strategies if user else []

@app.post("/strategies/{id}/toggle")
def toggle_strategy(id: int, db: Session = Depends(database.get_db)):
    strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    strat.is_running = not strat.is_running
    db.commit()
    return {"status": "OK", "is_running": strat.is_running}

@app.delete("/strategies/{id}")
def delete_strategy(id: int, db: Session = Depends(database.get_db)):
    db.query(models.Strategy).filter(models.Strategy.id == id).delete()
    db.commit()
    return {"status": "Deleted"}

@app.get("/strategies/{id}/logs")
def get_logs(id: int, db: Session = Depends(database.get_db)):
    return crud.get_strategy_logs(db, id)

@app.get("/strategy/{id}")
def get_strategy_details(id: int, db: Session = Depends(database.get_db)):
    return db.query(models.Strategy).filter(models.Strategy.id == id).first()

@app.put("/strategy/{id}")
def update_strategy(id: int, strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    db_strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    db_strat.name = strat.name
    db_strat.symbol = strat.symbol
    db_strat.broker = strat.broker # Update broker too
    db_strat.logic_configuration = strat.logic
    db.commit()
    return {"status": "Updated", "id": id}

@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    timeframe = strat.logic.get('timeframe', '1h')
    
    # ROUTE TO CORRECT DATA SOURCE
    if strat.broker == "COINDCX":
        df = await coindcx_manager.fetch_history(strat.symbol, timeframe, limit=3000)
    else:
        df = await backtester.fetch_historical_data(strat.symbol, timeframe, limit=3000)
    
    if df.empty: return {"error": f"No data for {strat.symbol} on {strat.broker}"}

    results = backtester.run_simulation(df, strat.logic)
    return results
