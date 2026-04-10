import os, re

print("🔌 Rerouting ALL Backtests through the Global Data Vault...")
os.system('docker cp app-backend-1:/app/main.py ./main.py')

with open('./main.py', 'r') as f:
    m = f.read()

# Locate the old API route that bypassed the Vault for CoinDCX
target = r"@app\.post\(\"/strategy/backtest\"\)\nasync def run_backtest\(strat: schemas\.StrategyInput\):[\s\S]*?if df\.empty: return \{\"error\": f\"No data for \{strat\.symbol\}\"\}"

# The new route that forces EVERY broker to check the Vault first
replacement = """@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    tf = strat.logic.get('timeframe', '1h')
    import os
    import pandas as pd
    
    # 1. Normalize Symbol for Vault lookup (e.g., BTCUSD -> BTCUSDT)
    clean_symbol = strat.symbol.replace("/", "").replace("-", "").replace("_", "")
    if clean_symbol.endswith('USD') and not clean_symbol.endswith('USDT'):
        clean_symbol = clean_symbol[:-3] + 'USDT'
        
    vault_path = f"/app/vault/{clean_symbol}_{tf}.parquet"
    
    # 2. GLOBAL VAULT INTERCEPT: Ignore broker selection if we have the massive dataset!
    if os.path.exists(vault_path):
        df = pd.read_parquet(vault_path)
    else:
        # VAULT MISS: Fallback to Live APIs for obscure altcoins
        if strat.broker.upper() == "COINDCX":
            from app.brokers.coindcx import coindcx_manager
            df = await coindcx_manager.fetch_history(strat.symbol, tf, limit=3000)
        else:
            from app.backtester import backtester
            df = await backtester.fetch_historical_data(strat.symbol, tf, limit=3000)
            
    if df is None or df.empty: return {"error": f"No data for {strat.symbol}"}"""

m = re.sub(target, replacement, m)

with open('./main.py', 'w') as f:
    f.write(m)
    
os.system('docker cp ./main.py app-backend-1:/app/main.py')
print("✅ Global Vault Routing successfully injected!")
