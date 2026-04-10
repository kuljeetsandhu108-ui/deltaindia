import os, re

print("💎 Converting system to Broker-Independent Pure Quant Mode...")

# --- STEP 1: BACKEND (main.py) ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: m = f.read()

# Unified Symbol List (Ignore broker parameter)
m = re.sub(r'async def get_symbols\(broker: str = "DELTA"\):[\s\S]*?return symbol_cache\[b\]', 
           'async def get_symbols():\n    import json, os\n    if os.path.exists("/app/coindcx_verified.json"):\n        with open("/app/coindcx_verified.json", "r") as f: return json.load(f)\n    return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]', m)

# Make Backtest Route broker-blind
m = m.replace('if strat.broker.upper() == "COINDCX":', 'if True: # Default to High-Granularity Fallback')

with open('./main.py', 'w') as f: f.write(m)
os.system('docker cp ./main.py app-backend-1:/app/main.py')


# --- STEP 2: AI PROMPT (route.ts) ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: a = f.read()

# Remove broker from required JSON fields
a = a.replace('- "broker": "DELTA" or "COINDCX".', '')
a = a.replace('"broker": "COINDCX",', '')

with open('./route.ts', 'w') as f: f.write(a)
os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')


# --- STEP 3: UI CLEANUP (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# Remove broker from fetch dependencies
p = p.replace('?broker=${broker}', '')
p = p.replace('[broker, editId]', '[editId]')
p = p.replace('[broker, symbol]', '[symbol]')

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ System is now Broker-Independent!")
