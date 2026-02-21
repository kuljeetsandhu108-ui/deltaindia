import ccxt.async_support as ccxt
import time
import asyncio
from . import database
from sqlalchemy import text

async def ping_delta():
    start = time.time()
    exchange = None
    try:
        # Ping Delta India specifically
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
    exchange = None
    try:
        exchange = ccxt.coindcx({'timeout': 10000})
        # Fetching markets is a reliable ping for CoinDCX
        await exchange.fetch_markets()
        latency = int((time.time() - start) * 1000)
        return {"status": "OK", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}
    finally:
        if exchange: await exchange.close()

def ping_database():
    start = time.time()
    try:
        db = database.SessionLocal()
        # Execute a raw SQL ping
        db.execute(text("SELECT 1"))
        db.close()
        latency = int((time.time() - start) * 1000)
        return {"status": "OK", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}

async def run_full_diagnostics():
    # Run network pings simultaneously for speed
    delta_res, coindcx_res = await asyncio.gather(ping_delta(), ping_coindcx())
    db_res = ping_database()
    
    return {
        "database": db_res,
        "delta_india": delta_res,
        "coindcx": coindcx_res
    }
