import os

print("🧠 Upgrading CoinDCX Stale Data Detector...")
os.system('docker cp app-backend-1:/app/app/brokers/coindcx.py ./coindcx.py')

with open('./coindcx.py', 'r') as f:
    c = f.read()

# The exact block we are upgrading
target = """            if data and isinstance(data, list):
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                return df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True).dropna().tail(limit)"""

# The upgraded block with the Stale Data check
replacement = """            if data and isinstance(data, list):
                df = pd.DataFrame(data)
                if 'time' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
                    cols = ['open', 'high', 'low', 'close', 'volume']
                    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True).dropna().tail(limit)
                    
                    if not df.empty:
                        import time
                        # 🛑 STALE DATA DETECTOR
                        # If CoinDCX returns data older than 48 hours, it's a dead API node. Throw it away!
                        latest_ms = int(pd.to_numeric(df['time']).max())
                        current_ms = int(time.time() * 1000)
                        if (current_ms - latest_ms) < 172800000: # 48 hours in ms
                            return df
                        else:
                            print(f"⚠️ CoinDCX API node is stale (Ends in {df.iloc[-1]['timestamp']}). Moving to Binance Liquidity...")"""

if target in c:
    c = c.replace(target, replacement)
    with open('./coindcx.py', 'w') as f:
        f.write(c)
    os.system('docker cp ./coindcx.py app-backend-1:/app/app/brokers/coindcx.py')
    print("✅ Stale Data Detector injected successfully!")
else:
    print("Target block not found. It may have already been patched.")
