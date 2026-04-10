import asyncio
import json
import requests
import urllib3
from app.brokers.coindcx import coindcx_manager

urllib3.disable_warnings()

async def run_sweep():
    print("🧹 Starting Deep Sweep of CoinDCX Pairs. This will filter out 'Ghost Pairs'...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Get the raw, unfiltered list of all pairs directly from the exchange
    resp = await asyncio.to_thread(requests.get, "https://api.coindcx.com/exchange/ticker", headers=headers, verify=False)
    raw_syms = [item.get('market', '') for item in resp.json()]
    symbols = sorted(list(set([s for s in raw_syms if s and ('USDT' in s or 'USD' in s)])))
    
    print(f"📊 Found {len(symbols)} total raw pairs. Testing historical data feeds now...\n")
    
    valid_pairs = []
    sem = asyncio.Semaphore(15) # Run 15 checks at the same time for speed
    
    async def check_pair(sym):
        async with sem:
            try:
                # We ask for just 5 candles. If it can't even give us 5, it's a ghost pair!
                df = await coindcx_manager.fetch_history(sym, timeframe='1h', limit=5)
                if df is not None and not df.empty:
                    valid_pairs.append(sym)
                    print(f"✅ {sym} -> HEALTHY")
                else:
                    print(f"❌ {sym} -> GHOST PAIR (Banned)")
            except:
                print(f"❌ {sym} -> API ERROR (Banned)")

    # Run all tests
    await asyncio.gather(*(check_pair(sym) for sym in symbols))
    
    # Save the healthy ones to a master Verified file
    with open('/app/coindcx_verified.json', 'w') as f:
        json.dump(sorted(valid_pairs), f)
        
    print(f"\n🎯 SWEEP COMPLETE! Kept {len(valid_pairs)} healthy pairs. Eliminated {len(symbols) - len(valid_pairs)} Ghost Pairs.")

if __name__ == "__main__":
    asyncio.run(run_sweep())
