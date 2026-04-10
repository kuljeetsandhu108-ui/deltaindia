import os

print("🏦 Injecting Portfolio Analysis Engine...")

with open('./main.py', 'r') as f:
    m = f.read()

portfolio_endpoint = """
@app.get("/user/{email}/portfolio")
async def get_portfolio(email: str, db: Session = Depends(database.get_db)):
    from app import security
    import ccxt.async_support as ccxt
    import time, hmac, hashlib, requests, asyncio
    
    user = crud.get_user_by_email(db, email)
    if not user: return {"error": "User not found"}
    
    portfolio = {
        "total_usdt": 0.0,
        "total_inr": 0.0,
        "assets": [],
        "positions": []
    }
    
    # --- 1. FETCH DELTA EXCHANGE ---
    if user.delta_api_key:
        try:
            dk = security.decrypt_value(user.delta_api_key)
            ds = security.decrypt_value(user.delta_api_secret)
            # Use CCXT for standard access
            exchange = ccxt.delta({
                'apiKey': dk, 'secret': ds, 
                'options': {'defaultType': 'future'}, 
                'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}
            })
            
            # Fetch Balance
            bal = await exchange.fetch_balance()
            usdt_free = float(bal.get('USDT', {}).get('free', 0))
            usdt_used = float(bal.get('USDT', {}).get('used', 0))
            total_delta = usdt_free + usdt_used
            
            portfolio["total_usdt"] += total_delta
            portfolio["assets"].append({"asset": "USDT (Delta)", "amount": total_delta, "source": "Delta"})
            
            # Fetch Positions
            positions = await exchange.fetch_positions()
            for p in positions:
                if float(p.get('contracts', 0)) > 0:
                    portfolio["positions"].append({
                        "symbol": p['symbol'],
                        "size": p['contracts'],
                        "entry": p['entryPrice'],
                        "pnl": p['unrealizedPnl'],
                        "broker": "Delta"
                    })
            await exchange.close()
        except Exception as e: print(f"Delta Error: {e}")

    # --- 2. FETCH COINDCX ---
    if user.coindcx_api_key:
        try:
            ck = security.decrypt_value(user.coindcx_api_key)
            cs = security.decrypt_value(user.coindcx_api_secret)
            
            # Fetch Balance via REST
            url = "https://api.coindcx.com/exchange/v1/users/balances"
            payload = {"timestamp": int(time.time() * 1000)}
            sig = hmac.new(bytes(cs, 'utf-8'), json.dumps(payload, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': ck, 'X-AUTH-SIGNATURE': sig}
            
            resp = await asyncio.to_thread(requests.post, url, data=json.dumps(payload, separators=(',', ':')), headers=headers)
            if resp.status_code == 200:
                for b in resp.json():
                    amt = float(b.get('balance', 0))
                    curr = b.get('currency')
                    if amt > 0:
                        # Simple estimation: Assume 1 USDT = 1 USD for consolidation
                        if curr == 'USDT': 
                            portfolio["total_usdt"] += amt
                        
                        portfolio["assets"].append({"asset": curr, "amount": amt, "source": "CoinDCX"})

        except Exception as e: print(f"CoinDCX Error: {e}")

    # Convert to INR (Approx 88 rate for display)
    portfolio["total_inr"] = portfolio["total_usdt"] * 88.0
    return portfolio
"""

if '/portfolio' not in m:
    m += portfolio_endpoint
    with open('./main.py', 'w') as f: f.write(m)

os.system('docker cp ./main.py app-backend-1:/app/main.py')
print("✅ Portfolio Engine Injected!")
