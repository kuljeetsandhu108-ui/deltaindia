import asyncio
import sys
from app.brokers.coindcx import coindcx_manager
from app.backtester import backtester

async def diagnose_pair(broker, symbol, timeframe="1h"):
    print(f"\n🩺 DATA DOCTOR DIAGNOSTIC: {broker} | {symbol} | {timeframe}")
    print("-" * 50)
    
    df = None
    if broker.upper() == "COINDCX":
        df = await coindcx_manager.fetch_history(symbol, timeframe, limit=1000)
    else:
        df = await backtester.fetch_historical_data(symbol, timeframe, limit=1000)
        
    if df is None or df.empty:
        print("❌ ERROR: Failed to fetch any data. The pair might be delisted or invalid.")
    else:
        print(f"✅ SUCCESS: Successfully fetched {len(df)} historical candles.")
        print(f"🕒 Oldest Candle: {df.iloc[0]['timestamp']}")
        print(f"🕒 Newest Candle: {df.iloc[-1]['timestamp']}")
        print(f"💵 Latest Close Price: ${df.iloc[-1]['close']}")
    print("-" * 50)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: docker exec app-backend-1 python3 data_doctor.py [BROKER] [SYMBOL]")
        print("Example: docker exec app-backend-1 python3 data_doctor.py COINDCX 0GUSDT")
    else:
        broker = sys.argv[1]
        symbol = sys.argv[2]
        asyncio.run(diagnose_pair(broker, symbol))
