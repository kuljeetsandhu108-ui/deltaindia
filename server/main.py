import asyncio
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app import models, database, schemas, crud
from app.engine import engine as trading_engine
from app.backtester import backtester
import ccxt.async_support as ccxt

# --- SAFETY NET: HARDCODED FALLBACK LIST ---
# If API fails, we use these standard Delta India symbols
DEFAULT_SYMBOLS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "BNB-USDT",
    "DOGE-USDT", "ADA-USDT", "MATIC-USDT", "LTC-USDT", "DOT-USDT",
    "SHIB-USDT", "AVAX-USDT", "LINK-USDT", "UNI-USDT", "ATOM-USDT"
]

# Initialize with defaults so the UI is never empty
symbol_cache = DEFAULT_SYMBOLS

async def refresh_symbols():
    global symbol_cache
    exchange = None
    try:
        print("... Fetching Symbols from Delta India ...")
        exchange = ccxt.delta({
            'options': { 'defaultType': 'future' },
            'urls': { 
                'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'},
                'www': 'https://india.delta.exchange'
            }
        })
        markets = await exchange.load_markets()
        
        # BROADER FILTER: Get ANY active market that is a Future/Swap
        live_symbols = []
        for symbol, market in markets.items():
            # Check if active
            if market.get('active'):
                # We prefer the 'id' (e.g. BTC-USDT) over the symbol (BTC/USDT:USDT)
                # because the ID is what we need to send orders.
                market_id = market.get('id', symbol)
                live_symbols.append(market_id)
        
        if len(live_symbols) > 0:
            symbol_cache = sorted(list(set(live_symbols)))
            print(f"✅ Loaded {len(symbol_cache)} Live Pairs from API")
        else:
            print("⚠️ API returned 0 symbols. Keeping Defaults.")
            
    except Exception as e:
        print(f"⚠️ Symbol Fetch Failed: {e}. Using Defaults.")
        # We keep the default list if API fails
    finally:
        if exchange: await exchange.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fetch symbols on startup
    await refresh_symbols()
    asyncio.create_task(trading_engine.start())
    yield
    trading_engine.is_running = False

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="AlgoTradeIndia Engine", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home(): return {"status": "System Online", "symbols": len(symbol_cache)}

@app.get("/data/symbols")
def get_symbols():
    return symbol_cache

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
        except: raise HTTPException(status_code=404, detail="Sync error.")
    return {"status": "Keys Saved"}

@app.post("/strategy/create")
def create_strategy(strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    new_strat = crud.create_strategy(db, strat)
    if not new_strat: raise HTTPException(status_code=404, detail="User not found")
    return {"status": "Deployed", "id": new_strat.id}

@app.get("/strategies/{email}")
def get_user_strategies(email: str, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email)
    if not user: return []
    return user.strategies

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
    strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    if not strat: raise HTTPException(status_code=404, detail="Not found")
    return strat

@app.put("/strategy/{id}")
def update_strategy(id: int, strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    db_strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    if not db_strat: raise HTTPException(status_code=404, detail="Not found")
    db_strat.name = strat.name
    db_strat.symbol = strat.symbol
    db_strat.logic_configuration = strat.logic
    db.commit()
    return {"status": "Updated", "id": id}

@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    timeframe = strat.logic.get('timeframe', '1h')
    df = await backtester.fetch_historical_data(strat.symbol, timeframe, limit=3000)
    if df.empty: return {"error": f"Could not fetch data for {strat.symbol}"}
    results = backtester.run_simulation(df, strat.logic)
    return results
