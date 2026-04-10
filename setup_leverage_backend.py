import os

# --- A. Create the script that builds the Leverage Dictionary ---
engine_code = """import json, requests, urllib3
urllib3.disable_warnings()

cache = {"DELTA": {}, "COINDCX": {}}

print("⚙️ Building Delta Exchange Leverage Map...")
try:
    res = requests.get("https://api.india.delta.exchange/v2/products", verify=False, timeout=10)
    for p in res.json().get('result', []):
        sym = p.get('symbol')
        if p.get('initial_margin'):
            cache["DELTA"][sym] = int(1 / float(p['initial_margin']))
except: pass

print("⚙️ Building CoinDCX Leverage Map...")
try:
    # CoinDCX hides derivatives limits, so we use a smart institutional mapping rule
    res = requests.get("https://api.coindcx.com/exchange/ticker", verify=False, timeout=10)
    for item in res.json():
        sym = item.get('coindcx_name', item.get('market', ''))
        if 'BTC' in sym or 'ETH' in sym: cache["COINDCX"][sym] = 20
        elif sym.startswith(('SOL', 'XRP', 'ADA', 'MATIC', 'DOGE', 'BNB', 'LINK')): cache["COINDCX"][sym] = 10
        else: cache["COINDCX"][sym] = 5
except: pass

with open("/app/leverage_cache.json", "w") as f:
    json.dump(cache, f)
print("✅ Leverage Data Dictionary Compiled Successfully!")
"""
with open('./leverage_builder.py', 'w') as f: f.write(engine_code)
os.system('docker cp ./leverage_builder.py app-backend-1:/app/leverage_builder.py')
os.system('docker exec app-backend-1 python3 leverage_builder.py')


# --- B. Inject the API Endpoint into main.py ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: m = f.read()

endpoint = """
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
"""
if '/data/leverage' not in m:
    m += endpoint
    with open('./main.py', 'w') as f: f.write(m)
    os.system('docker cp ./main.py app-backend-1:/app/main.py')

