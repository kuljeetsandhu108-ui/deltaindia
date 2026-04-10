import os, re

print("🔓 Stripping all artificial candle limits from the Engine...")
os.system('docker cp app-backend-1:/app/main.py ./main.py')

with open('./main.py', 'r') as f:
    m = f.read()

# The perfectly clean, limit-free API Route
unlimited_route = """@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    try:
        from app.backtester import backtester
        import os
        import pandas as pd
        import sys
        if '/app' not in sys.path: sys.path.append('/app')
        
        tf = strat.logic.get('timeframe', '1h')
        
        # Standardize symbol
        clean_symbol = strat.symbol.replace("/", "").replace("-", "").replace("_", "")
        if clean_symbol.endswith('USD') and not clean_symbol.endswith('USDT'):
            clean_symbol = clean_symbol[:-3] + 'USDT'
            
        from fast_vault import ensure_5_years_sync
        
        # 1. Fetch the FULL 5-Year Dataset from the Vault (No arbitrary candle limits)
        df = ensure_5_years_sync(clean_symbol, tf)
        
        s_date = strat.logic.get('startDate')
        e_date = strat.logic.get('endDate')
        
        # 2. CALENDAR CONTROL: If dates are provided, strictly filter by them.
        if s_date and e_date:
            df = df[(df['timestamp'] >= pd.to_datetime(s_date)) & (df['timestamp'] <= pd.to_datetime(e_date) + pd.Timedelta(days=1))]
            
        if df is None or df.empty: 
            return {"error": f"No market data found for {strat.symbol} in the selected date range."}
            
        # 3. Process the Data (Whether it's 100 candles or 2.6 million candles)
        res = backtester.run_simulation(df, strat.logic)
        
        if isinstance(res, dict) and "error" in res:
            return {"error": res["error"]}
        return res
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Engine Crash: {str(e)}"}
"""

# Replace the existing route
pattern = r'@app\.post\("/strategy/backtest"\)[\s\S]*?(?=\n@app|\Z)'
m = re.sub(pattern, unlimited_route, m)

with open('./main.py', 'w') as f: 
    f.write(m)

os.system('docker cp ./main.py app-backend-1:/app/main.py')
print("✅ All artificial candle limits have been completely removed!")
