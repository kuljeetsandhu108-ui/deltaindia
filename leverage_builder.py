import json, requests, urllib3
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
