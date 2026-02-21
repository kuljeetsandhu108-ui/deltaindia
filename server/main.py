import asyncio
import traceback
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app import models, database, schemas, crud
from app.engine import engine as trading_engine
from app.backtester import backtester
from app.brokers.coindcx import coindcx_manager
import ccxt.async_support as ccxt

# --- SEPARATED DUAL CACHE ---
symbol_cache = {
    "DELTA": ["BTC-USDT", "ETH-USDT", "SOL-USDT"],
    "COINDCX": ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
}

async def refresh_delta_symbols():
    global symbol_cache
    exchange = None
    try:
        exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
        markets = await exchange.load_markets()
        live_symbols = [m.get('id', k) for k, m in markets.items() if m.get('active') and ('USDT' in m.get('id', '') or 'USD' in m.get('id', ''))]
        if live_symbols: 
            symbol_cache["DELTA"] = sorted(list(set(live_symbols)))
            print(f"✅ Loaded Delta Pairs")
    except Exception as e: print(f"Delta Fetch Error: {e}")
    finally:
        if exchange: await exchange.close()

async def refresh_coindcx_symbols():
    global symbol_cache
    try:
        syms = await coindcx_manager.fetch_symbols()
        if syms and len(syms) > 0:
            symbol_cache["COINDCX"] = syms
    except Exception as e: print(f"CoinDCX Fetch Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load BOTH worlds on startup
    asyncio.create_task(refresh_delta_symbols())
    asyncio.create_task(refresh_coindcx_symbols())
    asyncio.create_task(trading_engine.start())
    yield
    trading_engine.is_running = False

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="AlgoTradeIndia Engine", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"🔥 FATAL ERROR: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"}, headers={"Access-Control-Allow-Origin": "*"})

@app.get("/")
def home(): return {"status": "System Online", "delta": len(symbol_cache["DELTA"]), "coindcx": len(symbol_cache["COINDCX"])}

# --- THE FIX: SMART SYMBOL ROUTER ---
@app.get("/data/symbols")
async def get_symbols(broker: str = "DELTA"):
    b = broker.upper()
    if b not in symbol_cache: b = "DELTA"
    
    # Lazy load if empty
    if len(symbol_cache[b]) <= 4:
        if b == "DELTA": await refresh_delta_symbols()
        elif b == "COINDCX": await refresh_coindcx_symbols()
        
    return symbol_cache[b]
# ------------------------------------

@app.post("/auth/sync")
def sync_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user: return crud.create_user(db=db, user=user)
    return {"status": "User exists", "id": db_user.id}

@app.post("/user/keys")
def save_keys(keys: schemas.BrokerKeys, db: Session = Depends(database.get_db)):
    updated = crud.update_broker_keys(db, keys)
    if not updated:
         new_user = schemas.UserCreate(email=keys.email, full_name="Trader", picture="")
         crud.create_user(db, new_user)
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
    if strat:
        strat.is_running = not strat.is_running
        db.commit()
    return {"status": "OK"}

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
    if db_strat:
        db_strat.name, db_strat.symbol, db_strat.broker, db_strat.logic_configuration = strat.name, strat.symbol, strat.broker, strat.logic
        db.commit()
    return {"status": "Updated", "id": id}

@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    tf = strat.logic.get('timeframe', '1h')
    # Route history fetch to proper broker
    if strat.broker.upper() == "COINDCX":
        df = await coindcx_manager.fetch_history(strat.symbol, tf, limit=3000)
    else:
        df = await backtester.fetch_historical_data(strat.symbol, tf, limit=3000)
        
    if df.empty: return {"error": f"No data for {strat.symbol} on {strat.broker}"}
    return backtester.run_simulation(df, strat.logic)
