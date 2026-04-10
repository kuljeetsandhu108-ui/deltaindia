import urllib.request

# FIX 1: Bypass Delta Exchange Security to fetch ALL pairs
with open('main.py', 'r') as f: m = f.read()
if 'import requests' not in m:
    m = m.replace('import traceback\nfrom fastapi', 'import traceback\nimport requests\nimport urllib3\nurllib3.disable_warnings()\nfrom fastapi')
delta_fix = '''async def refresh_delta_symbols():
    global symbol_cache
    try:
        resp = await asyncio.to_thread(requests.get, "https://api.india.delta.exchange/v2/products", verify=False, timeout=10)
        syms = [p["symbol"] for p in resp.json().get("result", []) if "USDT" in p["symbol"] or "USD" in p["symbol"]]
        if len(syms) > 5: symbol_cache["DELTA"] = sorted(list(set(syms)))
    except Exception as e: print(e)
    return
    try:
        exchange = ccxt.delta'''
m = m.replace('async def refresh_delta_symbols():\n    global symbol_cache\n    try:\n        exchange = ccxt.delta', delta_fix)
with open('main.py', 'w') as f: f.write(m)

# FIX 2: Activate Paper Trading logic in the Engine
with open('engine.py', 'r') as f: e = f.read()
e = e.replace('async def fire_order(self, db, strat_id, broker, symbol, side, qty, api_key_enc, secret_enc, price, reason):', 'async def fire_order(self, db, strat_id, broker, symbol, side, qty, api_key_enc, secret_enc, price, reason, trade_mode="LIVE"):')
target_1 = """        try:\n            api_key = security.decrypt_value(api_key_enc)"""
replace_1 = """        try:\n            if trade_mode == 'PAPER':\n                crud.create_log(db, strat_id, f"📄 PAPER TRADE: {reason} {side} {qty} {symbol} @ ${price}", "SUCCESS")\n                return True\n            api_key = security.decrypt_value(api_key_enc)"""
e = e.replace(target_1, replace_1)
e = e.replace("side = logic.get('side', 'BUY').upper()", "side = logic.get('side', 'BUY').upper()\n            trade_mode = logic.get('tradeMode', 'PAPER').upper()")
e = e.replace('current_price, "ENTRY")', 'current_price, "ENTRY", trade_mode)')
e = e.replace('current_price, f"EXIT ({reason})")', 'current_price, f"EXIT ({reason})", trade_mode)')
with open('engine.py', 'w') as f: f.write(e)

# FIX 3: Inject the Paper/Live Toggle directly into the Next.js UI
with open('page.tsx', 'r') as f: p = f.read()
if 'const [tradeMode' not in p:
    p = p.replace('const [side, setSide] = useState("BUY");', 'const [side, setSide] = useState("BUY");\n  const [tradeMode, setTradeMode] = useState("PAPER");')
    p = p.replace('setSide(logic.side || "BUY");', 'setSide(logic.side || "BUY");\n                    setTradeMode(logic.tradeMode || "PAPER");')
    p = p.replace('if (data.side) setSide(data.side.toUpperCase());', 'if (data.side) setSide(data.side.toUpperCase());\n            if (data.tradeMode) setTradeMode(data.tradeMode.toUpperCase());')
    p = p.replace('side, state: "WAITING"', 'side, tradeMode, state: "WAITING"')
    target_ui = """                <div>\n                  <label className="block text-sm text-slate-400 mb-1">Qty</label>"""
    replace_ui = """                <div>\n                    <label className="block text-sm text-slate-400 mb-1 flex items-center gap-2">Trading Mode</label>\n                    <select value={tradeMode} onChange={(e) => setTradeMode(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none font-bold text-emerald-400">\n                        <option value="PAPER">📄 PAPER TRADE (Safe)</option>\n                        <option value="LIVE">🔴 LIVE REAL MONEY</option>\n                    </select>\n                </div>\n                <div>\n                  <label className="block text-sm text-slate-400 mb-1">Qty</label>"""
    p = p.replace(target_ui, replace_ui)
    with open('page.tsx', 'w') as f: f.write(p)
