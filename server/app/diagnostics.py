import ccxt.async_support as ccxt
import time
import asyncio
import requests
from . import database
from sqlalchemy import text

async def ping_delta():
    start = time.time()
    exchange = None
    try:
        # Ping Delta India
        exchange = ccxt.delta({
            'urls': {
                'api': {'public': 'https://api.india.delta.exchange'},
                'www': 'https://india.delta.exchange'
            },
            'timeout': 10000
        })
        await exchange.fetch_time()
        latency = int((time.time() - start) * 1000)
        return {"status": "OK", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}
    finally:
        if exchange: await exchange.close()

async def ping_coindcx():
    start = time.time()
    try:
        # THE FIX: Bypass CCXT entirely for CoinDCX.
        # We use a direct HTTP request to their public markets endpoint as a "ping"
        url = "https://api.coindcx.com/exchange/v1/markets_details"
        
        # Run standard requests inside an async thread so it doesn't block the server
        response = await asyncio.to_thread(requests.get, url, timeout=10)
        
        if response.status_code == 200:
            latency = int((time.time() - start) * 1000)
            return {"status": "OK", "latency_ms": latency, "error": None}
        else:
            return {"status": "FAILED", "latency_ms": None, "error": f"HTTP Error {response.status_code}"}
            
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}

def ping_database():
    start = time.time()
    try:
        db = database.SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        latency = int((time.time() - start) * 1000)
        return {"status": "OK", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}

async def run_full_diagnostics():
    delta_res, coindcx_res = await asyncio.gather(ping_delta(), ping_coindcx())
    db_res = ping_database()
    
    return {
        "database": db_res,
        "delta_india": delta_res,
        "coindcx": coindcx_res
    }
