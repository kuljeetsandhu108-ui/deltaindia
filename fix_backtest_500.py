import os, re

print("🩹 Applying robust Error Handling & Data Caps to Backtester...")
os.system('docker cp app-backend-1:/app/main.py ./main.py')

with open('main.py', 'r') as f:
    m = f.read()

# The indestructible, shielded API Route
safe_route = """@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    try:
        from app.backtester import backtester
        import os
        import pandas as pd
        
        tf = strat.logic.get('timeframe', '1h')
        
        # Standardize symbol to match the vault perfectly
        clean_symbol = strat.symbol.replace("/", "").replace("-", "").replace("_", "")
        if clean_symbol.endswith('USD') and not clean_symbol.endswith('USDT'):
            clean_symbol = clean_symbol[:-3] + 'USDT'
            
        vault_path = f"/app/vault/{clean_symbol}_{tf}.parquet"
        
        df = None
        if os.path.exists(vault_path):
            df = pd.read_parquet(vault_path)
            # 🛡️ THE CPU SHIELD: Cap UI backtests at 15,000 candles (~2 years of 1h data)
            # This prevents the server from timing out on massive 5-year calculations!
            if len(df) > 15000:
                df = df.tail(15000).reset_index(drop=True)
        else:
            if strat.broker.upper() == "COINDCX":
                from app.brokers.coindcx import coindcx_manager
                df = await coindcx_manager.fetch_history(strat.symbol, tf, limit=3000)
            else:
                df = await backtester.fetch_historical_data(strat.symbol, tf, limit=3000)
                
        if df is None or df.empty: 
            return {"error": f"No historical data found for {strat.symbol}"}
            
        # Run the heavy Pandas simulation safely
        res = backtester.run_simulation(df, strat.logic)
        
        # Pass engine errors gracefully to the UI
        if isinstance(res, dict) and "error" in res:
            return {"error": res["error"]}
            
        return res
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Engine Crash: {str(e)}"}
"""

# Replace the old fragile route using a safe Regex boundary
pattern = r'@app\.post\("/strategy/backtest"\)[\s\S]*?(?=\n@app|\Z)'
m = re.sub(pattern, safe_route, m)

with open('main.py', 'w') as f: 
    f.write(m)

os.system('docker cp ./main.py app-backend-1:/app/main.py')
print("✅ Route upgraded successfully!")
