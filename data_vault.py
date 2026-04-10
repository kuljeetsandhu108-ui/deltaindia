import os
import time
import requests
import pandas as pd
from datetime import datetime

# Create the ultra-fast storage directory
VAULT_DIR = "/app/vault"
os.makedirs(VAULT_DIR, exist_ok=True)

def fetch_binance_data(symbol, interval, start_time_ms, end_time_ms):
    url = "https://fapi.binance.com/fapi/v1/klines"
    all_data = []
    current_start = start_time_ms
    
    print(f"🌐 Contacting Binance Core for {symbol} ({interval})...")
    
    while current_start < end_time_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_time_ms,
            "limit": 1000
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            
            # Break if error or no data
            if not data or type(data) is dict: 
                break
            
            all_data.extend(data)
            current_start = data[-1][0] + 1 # Advance to the exact next millisecond
            
            # Print progress seamlessly
            latest_date = pd.to_datetime(data[-1][0], unit='ms')
            print(f"   ⬇️ Downloaded data up to: {latest_date}")
            
            time.sleep(0.1) # Respect Binance API rate limits so we never get banned
        except Exception as e:
            print(f"❌ Error fetching: {e}")
            break
            
    return all_data

def update_vault(symbol, interval, years=5):
    print("="*60)
    print(f"🏦 ALGOEASE DATA VAULT: {symbol} | {interval}")
    print("="*60)
    
    file_path = f"{VAULT_DIR}/{symbol}_{interval}.parquet"
    now_ms = int(time.time() * 1000)
    
    if os.path.exists(file_path):
        print(f"📂 Existing Vault file found. Loading into memory...")
        df = pd.read_parquet(file_path)
        last_timestamp = int(df['timestamp'].max().timestamp() * 1000)
        print(f"🔄 Syncing missing data from {df['timestamp'].max()} to NOW...")
        start_ms = last_timestamp + 1
    else:
        print(f"🚀 Creating new Vault for {symbol} (Fetching last {years} years)...")
        start_ms = now_ms - (years * 365 * 24 * 60 * 60 * 1000)
        df = pd.DataFrame()
        
    if start_ms >= now_ms:
        print("✅ Vault is already 100% up to date!")
        return
        
    new_raw_data = fetch_binance_data(symbol, interval, start_ms, now_ms)
    
    if new_raw_data:
        new_df = pd.DataFrame(new_raw_data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
        ])
        new_df['timestamp'] = pd.to_datetime(new_df['time'], unit='ms')
        cols = ['open', 'high', 'low', 'close', 'volume']
        new_df[cols] = new_df[cols].apply(pd.to_numeric, errors='coerce')
        new_df = new_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        print("🧬 Stitching arrays and compressing to Parquet...")
        # Stitch old data and new data, drop duplicates, sort chronologically
        combined = pd.concat([df, new_df]).drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        # Save to ultra-fast Parquet format
        combined.to_parquet(file_path, engine='pyarrow')
        print(f"✅ SUCCESS: Saved {len(combined):,} total rows to Vault -> {file_path}")
    else:
        print("✅ No new data needed.")
    print("="*60)

if __name__ == "__main__":
    import sys
    # Default to BTCUSDT 1h if no arguments are passed
    sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    tf = sys.argv[2] if len(sys.argv) > 2 else "1h"
    update_vault(sym, tf, years=5)
