import os, re

print("🔌 Wiring the 5-Year Data Vault to the Backtesting Engine...")
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')

with open('./backtester.py', 'r') as f:
    b = f.read()

# The smart logic to intercept the request and check the Vault first
vault_logic = """    async def fetch_historical_data(self, symbol, timeframe='1h', limit=3000):
        import os
        import pandas as pd
        
        # Standardize the symbol name to match the Vault (e.g., BTC-USD -> BTCUSDT)
        clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
        if clean_symbol.endswith('USD') and not clean_symbol.endswith('USDT'):
            clean_symbol = clean_symbol[:-3] + 'USDT'
            
        tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
        tf = tf_map.get(timeframe, '1h')
        
        vault_path = f"/app/vault/{clean_symbol}_{tf}.parquet"
        
        # 🏦 THE VAULT INTERCEPT: If we have the massive dataset, load it instantly!
        if os.path.exists(vault_path):
            print(f"🏦 VAULT HIT: Loading massive 5-Year dataset for {clean_symbol}_{tf}...")
            df = pd.read_parquet(vault_path)
            return df

        # 🌐 VAULT MISS: Safe fallback to the live APIs for altcoins we haven't downloaded yet
        exchange = None"""

# Replace the start of the function perfectly
target = r"    async def fetch_historical_data\(self, symbol, timeframe='1h', limit=3000\):[\s\S]*?exchange = None"
b = re.sub(target, vault_logic, b)

with open('./backtester.py', 'w') as f:
    f.write(b)
    
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ Vault successfully wired to the Backtester!")
