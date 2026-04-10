import os, re

print("Injecting Quantitative Warmup Slice...")

# --- 1. Clean up Engine.py ---
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()

# Remove the experimental TradingView hack and restore standard, perfectly stable Pandas EWM
e = re.sub(r'    def calc_tv_ema.*?return pd\.Series\(ema, index=series\.index\)\n', '', e, flags=re.DOTALL)
e = re.sub(r"elif name == 'ema':[\s\S]*?return self\.calc_tv_ema\(df\['close'\], length\)", "elif name == 'ema': return df['close'].ewm(span=length, adjust=False).mean()", e)
e = re.sub(r"elif name == 'macd':[\s\S]*?return self\.calc_tv_ema.*?s\)", "elif name == 'macd':\n                f, s = int(params.get('fast', 12)), int(params.get('slow', 26))\n                return df['close'].ewm(span=f, adjust=False).mean() - df['close'].ewm(span=s, adjust=False).mean()", e)

with open('./engine.py', 'w') as f: f.write(e)
os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')


# --- 2. Clean up and Upgrade Backtester.py ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

b = re.sub(r'    def calc_tv_ema.*?return pd\.Series\(ema, index=series\.index\)\n', '', b, flags=re.DOTALL)
b = re.sub(r"elif name == 'ema':[\s\S]*?df\[col_name\] = self\.calc_tv_ema\(df\['close'\], length\)", "elif name == 'ema': df[col_name] = df['close'].ewm(span=length, adjust=False).mean()", b)
b = re.sub(r"elif name == 'macd':[\s\S]*?df\[col_name\] = self\.calc_tv_ema.*?s\)", "elif name == 'macd':\n                        f, s = int(params.get('fast', 12)), int(params.get('slow', 26))\n                        df[col_name] = df['close'].ewm(span=f, adjust=False).mean() - df['close'].ewm(span=s, adjust=False).mean()", b)

# INJECT THE WARMUP SLICE: Throw away the first 200 unstable candles before simulating
warmup_code = """            if df.empty: return {"error": "No Market Data"}
            df = self.prepare_data(df, logic)
            
            # --- INSTITUTIONAL WARMUP SLICE ---
            # Throw away the first 200 candles so EMAs have time to perfectly stabilize
            if len(df) > 200:
                df = df.iloc[200:].reset_index(drop=True)
            
            balance, start_price = 1000.0, float(df.iloc[0]['close'])"""

b = re.sub(r'            if df\.empty: return \{"error": "No Market Data"\}\n            df = self\.prepare_data\(df, logic\)\n\s*balance, start_price = 1000\.0, float\(df\.iloc\[0\]\[\'close\'\]\)', warmup_code, b)

with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')

print("✅ Math cleaned and Warmup Slice injected!")
