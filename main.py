import asyncio
import traceback
import requests
import urllib3
urllib3.disable_warnings()
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

# CACHE
symbol_cache = {
    "DELTA": ["BTC-USDT", "ETH-USDT"],
    "COINDCX": ["BTCUSDT", "ETHUSDT"] # Start with fallback
}

async def refresh_delta_symbols():
    global symbol_cache
    try:
        resp = await asyncio.to_thread(requests.get, "https://api.india.delta.exchange/v2/products", verify=False, timeout=10)
        syms = [p["symbol"] for p in resp.json().get("result", []) if "USDT" in p["symbol"] or "USD" in p["symbol"]]
        if len(syms) > 5: symbol_cache["DELTA"] = sorted(list(set(syms)))
    except Exception as e: print(e)
    return
    try:
        exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
        markets = await exchange.load_markets()
        syms = [m.get('id', k) for k, m in markets.items() if m.get('active') and ('USDT' in m.get('id', '') or 'USD' in m.get('id', ''))]
        if syms: symbol_cache["DELTA"] = sorted(list(set(syms)))
        await exchange.close()
    except: pass

async def refresh_coindcx_symbols():
    global symbol_cache
    try:
        # Call the manager
        syms = await coindcx_manager.fetch_symbols()
        # Only update if we got a real list (more than 2 defaults)
        if syms and len(syms) > 2:
            symbol_cache["COINDCX"] = syms
    except Exception as e: print(f"CoinDCX Init Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(refresh_delta_symbols())
    asyncio.create_task(refresh_coindcx_symbols())
    asyncio.create_task(trading_engine.start())
    yield
    trading_engine.is_running = False

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="AlgoTradeIndia Engine", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home(): return {"status": "Online"}

@app.get("/data/symbols")
async def get_symbols():
    import json, os
    if os.path.exists("/app/coindcx_verified.json"):
        with open("/app/coindcx_verified.json", "r") as f: return json.load(f)
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

@app.post("/auth/sync")
def sync_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user: return crud.create_user(db=db, user=user)
    return {"status": "User exists", "id": db_user.id}

@app.post("/user/keys")
def save_keys(keys: schemas.BrokerKeys, db: Session = Depends(database.get_db)):
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
    return {"status": "OK", "is_running": strat.is_running}

@app.delete("/strategies/{id}")
def delete_strategy(id: int, db: Session = Depends(database.get_db)):
    strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    if strat: db.delete(strat)
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
    try:
        from app.backtester import backtester
        import os
        import pandas as pd
        import sys
        if '/app' not in sys.path: sys.path.append('/app')
        
        tf = strat.logic.get('timeframe', '1h')
        
        # Standardize symbol
        clean_symbol = strat.symbol.replace("/", "").replace("-", "").replace("_", "")
        if clean_symbol.endswith('USD') and not clean_symbol.endswith('USDT'):
            clean_symbol = clean_symbol[:-3] + 'USDT'
            
        from fast_vault import ensure_5_years_sync
        
        # 1. Fetch the FULL 5-Year Dataset from the Vault (No arbitrary candle limits)
        df = ensure_5_years_sync(clean_symbol, tf)
        

            
        if df is None or df.empty: 
            return {"error": f"No market data found for {strat.symbol} in the selected date range."}
            
        # 3. Process the Data (Whether it's 100 candles or 2.6 million candles)
        res = backtester.run_simulation(df, strat.logic)
        
        if isinstance(res, dict) and "error" in res:
            return {"error": res["error"]}
        return res
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Engine Crash: {str(e)}"}

@app.get("/system/diagnostics")
async def get_system_diagnostics():
    return await run_full_diagnostics()

@app.get("/data/leverage")
async def get_leverage(broker: str = "DELTA", symbol: str = "BTCUSDT"):
    b = broker.upper()
    try:
        import json, os
        if os.path.exists("/app/leverage_cache.json"):
            with open("/app/leverage_cache.json", "r") as f:
                cache = json.load(f)
                return {"max_leverage": cache.get(b, {}).get(symbol, 20 if b == 'COINDCX' else 100)}
    except: pass
    return {"max_leverage": 20 if b == "COINDCX" else 100}

@app.get("/user/{email}/verify-keys")
async def verify_user_keys(email: str, db: Session = Depends(database.get_db)):
    from app import security
    import ccxt.async_support as ccxt
    import time, hmac, hashlib, requests, json, asyncio
    
    user = crud.get_user_by_email(db, email)
    if not user: return {"error": "User not found"}
    
    res = {"delta": {"status": "UNTESTED"}, "coindcx": {"status": "UNTESTED"}}
    
    # 1. Verify Delta
    if user.delta_api_key and user.delta_api_secret:
        try:
            dk = security.decrypt_value(user.delta_api_key)
            ds = security.decrypt_value(user.delta_api_secret)
            exchange = ccxt.delta({'apiKey': dk, 'secret': ds, 'options': {'defaultType': 'future'}, 'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}})
            await exchange.fetch_balance()
            await exchange.close()
            res["delta"] = {"status": "OK", "error": None}
        except Exception as e:
            err_msg = str(e).split(':')[-1].strip()[:100]
            res["delta"] = {"status": "FAILED", "error": err_msg}
    else:
        res["delta"] = {"status": "FAILED", "error": "Keys not saved in vault yet."}
        
    # 2. Verify CoinDCX
    if user.coindcx_api_key and user.coindcx_api_secret:
        try:
            ck = security.decrypt_value(user.coindcx_api_key)
            cs = security.decrypt_value(user.coindcx_api_secret)
            url = "https://api.coindcx.com/exchange/v1/users/balances"
            payload = {"timestamp": int(time.time() * 1000)}
            json_payload = json.dumps(payload, separators=(',', ':'))
            signature = hmac.new(bytes(cs, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': ck, 'X-AUTH-SIGNATURE': signature}
            resp = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
            if resp.status_code == 200:
                res["coindcx"] = {"status": "OK", "error": None}
            else:
                msg = resp.json().get('message', f'HTTP Error {resp.status_code}')
                res["coindcx"] = {"status": "FAILED", "error": msg}
        except Exception as e:
            res["coindcx"] = {"status": "FAILED", "error": str(e)[:100]}
    else:
        res["coindcx"] = {"status": "FAILED", "error": "Keys not saved in vault yet."}
        
    return res

@app.get("/user/{email}/portfolio")
async def get_portfolio(email: str, db: Session = Depends(database.get_db)):
    from app import security
    import ccxt.async_support as ccxt
    import time, hmac, hashlib, requests, asyncio
    
    user = crud.get_user_by_email(db, email)
    if not user: return {"error": "User not found"}
    
    portfolio = {
        "total_usdt": 0.0,
        "total_inr": 0.0,
        "assets": [],
        "positions": []
    }
    
    # --- 1. FETCH DELTA EXCHANGE ---
    if user.delta_api_key:
        try:
            dk = security.decrypt_value(user.delta_api_key)
            ds = security.decrypt_value(user.delta_api_secret)
            # Use CCXT for standard access
            exchange = ccxt.delta({
                'apiKey': dk, 'secret': ds, 
                'options': {'defaultType': 'future'}, 
                'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}
            })
            
            # Fetch Balance
            bal = await exchange.fetch_balance()
            usdt_free = float(bal.get('USDT', {}).get('free', 0))
            usdt_used = float(bal.get('USDT', {}).get('used', 0))
            total_delta = usdt_free + usdt_used
            
            portfolio["total_usdt"] += total_delta
            portfolio["assets"].append({"asset": "USDT (Delta)", "amount": total_delta, "source": "Delta"})
            
            # Fetch Positions
            positions = await exchange.fetch_positions()
            for p in positions:
                if float(p.get('contracts', 0)) > 0:
                    portfolio["positions"].append({
                        "symbol": p['symbol'],
                        "size": p['contracts'],
                        "entry": p['entryPrice'],
                        "pnl": p['unrealizedPnl'],
                        "broker": "Delta"
                    })
            await exchange.close()
        except Exception as e: print(f"Delta Error: {e}")

    # --- 2. FETCH COINDCX ---
    if user.coindcx_api_key:
        try:
            ck = security.decrypt_value(user.coindcx_api_key)
            cs = security.decrypt_value(user.coindcx_api_secret)
            
            # Fetch Balance via REST
            url = "https://api.coindcx.com/exchange/v1/users/balances"
            payload = {"timestamp": int(time.time() * 1000)}
            sig = hmac.new(bytes(cs, 'utf-8'), json.dumps(payload, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': ck, 'X-AUTH-SIGNATURE': sig}
            
            resp = await asyncio.to_thread(requests.post, url, data=json.dumps(payload, separators=(',', ':')), headers=headers)
            if resp.status_code == 200:
                for b in resp.json():
                    amt = float(b.get('balance', 0))
                    curr = b.get('currency')
                    if amt > 0:
                        # Simple estimation: Assume 1 USDT = 1 USD for consolidation
                        if curr == 'USDT': 
                            portfolio["total_usdt"] += amt
                        
                        portfolio["assets"].append({"asset": curr, "amount": amt, "source": "CoinDCX"})

        except Exception as e: print(f"CoinDCX Error: {e}")

    # Convert to INR (Approx 88 rate for display)
    portfolio["total_inr"] = portfolio["total_usdt"] * 88.0
    return portfolio

@app.get("/auth/check-access/{email}")
def check_access(email: str, db: Session = Depends(database.get_db)):
    from app.models import Whitelist
    user = db.query(Whitelist).filter(Whitelist.email == email.lower()).first()
    return {"authorized": True if user else False}
