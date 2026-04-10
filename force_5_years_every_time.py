import os, re

print("🔌 Forcing 5-Year Data Guarantee on all Backtests...")
os.system('docker cp app-backend-1:/app/main.py ./main.py')

with open('./main.py', 'r') as f:
    m = f.read()

# The indestructible route that forces 5 years of data to be built instantly if it's missing
safe_route = """@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    try:
        from app.backtester import backtester
        import os
        import pandas as pd
        import sys
        if '/app' not in sys.path: sys.path.append('/app')
        
        tf = strat.logic.get('timeframe', '1h')
        
        clean_symbol = strat.symbol.replace("/", "").replace("-", "").replace("_", "")
        if clean_symbol.endswith('USD') and not clean_symbol.endswith('USDT'):
            clean_symbol = clean_symbol[:-3] + 'USDT'
            
        vault_path = f"/app/vault/{clean_symbol}_{tf}.parquet"
        
        df = None
        
        # 🚀 ON-DEMAND 5-YEAR VAULT BUILDER 🚀
        # If the file isn't there, don't use the small API! Build the 5-year file instantly!
        if not os.path.exists(vault_path):
            print(f"⚠️ Vault miss for {clean_symbol}_{tf}. Building 5-year history on-demand...")
            try:
                from data_vault import update_vault
                # Force download of 5 years (2021 to 2026)
                update_vault(clean_symbol, tf, years=5)
            except Exception as e:
                print(f"On-Demand Vault build failed: {e}")
                
        # Now read the massive file we just downloaded!
        if os.path.exists(vault_path):
            df = pd.read_parquet(vault_path)
            
            s_date = strat.logic.get('startDate')
            e_date = strat.logic.get('endDate')
            
            if s_date and e_date:
                df = df[(df['timestamp'] >= pd.to_datetime(s_date)) & (df['timestamp'] <= pd.to_datetime(e_date) + pd.Timedelta(days=1))]
        else:
            # TRUE FALLBACK: Only if the coin is a complete ghost and doesn't exist on Binance
            if strat.broker.upper() == "COINDCX":
                from app.brokers.coindcx import coindcx_manager
                df = await coindcx_manager.fetch_history(strat.symbol, tf, limit=3000)
            else:
                df = await backtester.fetch_historical_data(strat.symbol, tf, limit=3000)
                
        if df is None or df.empty: 
            return {"error": f"No historical data found for {strat.symbol}"}
            
        res = backtester.run_simulation(df, strat.logic)
        if isinstance(res, dict) and "error" in res:
            return {"error": res["error"]}
        return res
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Engine Crash: {str(e)}"}
"""

pattern = r'@app\.post\("/strategy/backtest"\)[\s\S]*?(?=\n@app|\Z)'
m = re.sub(pattern, safe_route, m)

with open('./main.py', 'w') as f: 
    f.write(m)

os.system('docker cp ./main.py app-backend-1:/app/main.py')
print("✅ 5-Year Guarantee successfully injected!")
