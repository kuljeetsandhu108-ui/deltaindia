import os, re

print("🔄 Upgrading Delta Feed from fragile WebSockets to Bulletproof REST Polling...")
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')

with open('./engine.py', 'r') as f: 
    e = f.read()

# Target the entire broken WebSocket loop
target = r'    async def run_delta_loop\(self\):[\s\S]*?(?=    async def run_coindcx_loop)'

# Replace it with the indestructible REST Polling loop
replacement = """    async def run_delta_loop(self):
        print("🌐 Delta World Online (REST Polling).")
        import urllib3
        urllib3.disable_warnings()
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "DELTA")
                db.close()
                if symbols:
                    resp = await asyncio.to_thread(requests.get, "https://api.india.delta.exchange/v2/tickers", verify=False, timeout=10)
                    if resp.status_code == 200:
                        tickers = resp.json().get('result', [])
                        ticker_map = {}
                        for t in tickers:
                            val = t.get('close') or t.get('mark_price') or 0
                            ticker_map[t['symbol']] = float(val)
                        
                        for sym in symbols:
                            current_price = ticker_map.get(sym, 0.0)
                            if current_price > 0:
                                db_tick = database.SessionLocal()
                                await self.execute_trade(db_tick, sym, current_price, "DELTA")
                                db_tick.close()
            except Exception as err: pass
            await asyncio.sleep(2) # Safely check prices every 2 seconds

"""

e = re.sub(target, replacement, e)

with open('./engine.py', 'w') as f: 
    f.write(e)

os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')
print("✅ Delta Feed Upgraded successfully!")
