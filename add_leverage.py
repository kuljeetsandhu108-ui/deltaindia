import re, os

print("Injecting Dynamic Leverage & Wallet % features...")

# --- 1. FRONTEND UI UPGRADE ---
with open('page.tsx', 'r') as f: p = f.read()
if 'const [walletPct' not in p:
    p = p.replace('const [tradeMode, setTradeMode] = useState("PAPER");', 'const [tradeMode, setTradeMode] = useState("PAPER");\n  const [walletPct, setWalletPct] = useState(10);\n  const [leverage, setLeverage] = useState(1);')
    p = p.replace('setTradeMode(logic.tradeMode || "PAPER");', 'setTradeMode(logic.tradeMode || "PAPER");\n                    setWalletPct(logic.walletPct || 10);\n                    setLeverage(logic.leverage || 1);')
    p = p.replace('if (data.tradeMode) setTradeMode(data.tradeMode.toUpperCase());', 'if (data.tradeMode) setTradeMode(data.tradeMode.toUpperCase());\n            if (data.walletPct) setWalletPct(data.walletPct);\n            if (data.leverage) setLeverage(data.leverage);')
    p = p.replace('quantity: Number(quantity),', 'walletPct: Number(walletPct), leverage: Number(leverage),')

    # Replace Qty UI with Leverage & Wallet %
    replace_ui = """                <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1">Leverage (x)</label>
                      <input type="number" value={leverage} onChange={(e) => setLeverage(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none text-yellow-400 font-bold" />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1">% of Wallet</label>
                      <input type="number" value={walletPct} onChange={(e) => setWalletPct(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none text-cyan-400 font-bold" />
                    </div>
                </div>"""
    p = re.sub(r'<div>\s*<label className="block text-sm text-slate-400 mb-1">Qty</label>\s*<input type="number" value=\{quantity\}.*?</div>', replace_ui, p, flags=re.DOTALL)
    with open('page.tsx', 'w') as f: f.write(p)

# --- 2. AI GENERATOR UPGRADE ---
with open('route.ts', 'r') as f: r = f.read()
if 'walletPct' not in r:
    r = r.replace('- "quantity": Number (default 1).', '- "walletPct": Number (default 10 for 10% of wallet).\n    - "leverage": Number (default 1).')
    r = r.replace('"quantity": 1,', '"walletPct": 10,\n      "leverage": 1,')
    with open('route.ts', 'w') as f: f.write(r)

# --- 3. LIVE ENGINE UPGRADE ---
with open('engine.py', 'r') as f: e = f.read()
if 'async def get_balance' not in e:
    balance_func = """
    async def get_balance(self, broker, api_key_enc, secret_enc):
        try:
            api_key = security.decrypt_value(api_key_enc)
            secret = security.decrypt_value(secret_enc)
            if broker == "DELTA":
                exchange = ccxt.delta({'apiKey': api_key, 'secret': secret, 'options': { 'defaultType': 'future' }, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}})
                bal = await exchange.fetch_balance()
                await exchange.close()
                return float(bal.get('USDT', {}).get('free', 0))
            elif broker == "COINDCX":
                url = "https://api.coindcx.com/exchange/v1/users/balances"
                payload = {"timestamp": int(time.time() * 1000)}
                json_payload = json.dumps(payload, separators=(',', ':'))
                signature = hmac.new(bytes(secret, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
                headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': api_key, 'X-AUTH-SIGNATURE': signature}
                resp = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
                if resp.status_code == 200:
                    balances = resp.json()
                    for b in balances:
                        if b.get('currency') == 'USDT': return float(b.get('balance', 0))
            return 0.0
        except Exception as err:
            print(f"Balance Fetch Error: {err}")
            return 0.0

    async def execute_trade"""
    e = e.replace('    async def execute_trade', balance_func)

    # Calculate Qty dynamically for Entry
    e = e.replace("qty = float(logic.get('quantity', 1))", "wallet_pct = float(logic.get('walletPct', 10))\n            leverage = float(logic.get('leverage', 1))\n            trade_mode = logic.get('tradeMode', 'PAPER').upper()")
    
    target_entry = """                    crud.create_log(db, strat.id, f"🚀 Firing ENTRY {side} for {qty} {symbol}", "INFO")
                    success = await self.fire_order(db, strat.id, broker, symbol, side, qty, api_key_enc, secret_enc, current_price, "ENTRY", trade_mode)"""
    replace_entry = """                    if trade_mode == 'LIVE':
                        balance = await self.get_balance(broker, api_key_enc, secret_enc)
                    else:
                        balance = 1000.0 # Paper trade default balance
                    
                    if balance <= 0:
                        crud.create_log(db, strat.id, f"❌ Insufficient Balance. Cannot execute.", "ERROR")
                        continue

                    trade_value = balance * (wallet_pct / 100.0) * leverage
                    qty = round(trade_value / current_price, 4)

                    crud.create_log(db, strat.id, f"🚀 ENTRY {side} {symbol} | Lev: {leverage}x | Qty: {qty}", "INFO")
                    success = await self.fire_order(db, strat.id, broker, symbol, side, qty, api_key_enc, secret_enc, current_price, "ENTRY", trade_mode)"""
    e = e.replace(target_entry, replace_entry)

    # Store entry Qty for Exit
    e = e.replace("logic['entry_price'] = current_price", "logic['entry_price'] = current_price\n                        logic['entry_qty'] = qty")
    
    # Retrieve entry Qty for Exit
    target_exit = """                if exit_triggered:
                    exit_side = 'SELL' if side == 'BUY' else 'BUY'
                    crud.create_log(db, strat.id, f"🏁 EXIT Condition Met ({reason}). Firing {exit_side}...", "INFO")
                    success = await self.fire_order(db, strat.id, broker, symbol, exit_side, qty, api_key_enc, secret_enc, current_price, f"EXIT ({reason})", trade_mode)"""
    replace_exit = """                if exit_triggered:
                    exit_side = 'SELL' if side == 'BUY' else 'BUY'
                    qty = float(logic.get('entry_qty', 1))
                    crud.create_log(db, strat.id, f"🏁 EXIT {reason} hit. Firing {exit_side} {qty}...", "INFO")
                    success = await self.fire_order(db, strat.id, broker, symbol, exit_side, qty, api_key_enc, secret_enc, current_price, f"EXIT ({reason})", trade_mode)"""
    e = e.replace(target_exit, replace_exit)
    with open('engine.py', 'w') as f: f.write(e)

# --- 4. BACKTESTER UPGRADE ---
with open('backtester.py', 'r') as f: b = f.read()
if "wallet_pct =" not in b:
    b = b.replace("qty, sl_pct, tp_pct = float(logic.get('quantity', 1)), float(logic.get('sl', 0)), float(logic.get('tp', 0))", "wallet_pct, leverage = float(logic.get('walletPct', 10)), float(logic.get('leverage', 1))\n            sl_pct, tp_pct = float(logic.get('sl', 0)), float(logic.get('tp', 0))")
    
    target_bt_entry = """                        balance -= (float(row['close']) * qty * FEE)
                        position = {'entry_price': float(row['close']), 'qty': qty, 'entry_time': row['timestamp']}"""
    replace_bt_entry = """                        trade_value = balance * (wallet_pct / 100.0) * leverage
                        qty = trade_value / float(row['close'])
                        balance -= (trade_value * FEE)
                        position = {'entry_price': float(row['close']), 'qty': qty, 'entry_time': row['timestamp']}"""
    b = b.replace(target_bt_entry, replace_bt_entry)
    with open('backtester.py', 'w') as f: f.write(b)

print("✅ Patch Complete!")
