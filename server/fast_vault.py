import concurrent.futures
import requests, time, os
import pandas as pd

VAULT_DIR = "/app/vault"
os.makedirs(VAULT_DIR, exist_ok=True)

def fetch_chunk(symbol, tf, start, end):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": tf, "startTime": start, "endTime": end, "limit": 1000}
    for _ in range(3):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200: return resp.json()
        except: time.sleep(0.5)
    return[]

def ensure_5_years_sync(symbol, tf):
    file_path = f"{VAULT_DIR}/{symbol}_{tf}.parquet"
    now_ms = int(time.time() * 1000)
    # Exactly 5 years in milliseconds
    # Exactly January 1, 2021 00:00:00 UTC
    start_ms = 1609459200000
    
    df = pd.DataFrame()
    if os.path.exists(file_path):
        df = pd.read_parquet(file_path)
        if not df.empty:
            last_ms = int(df['timestamp'].max().timestamp() * 1000)
            if last_ms > start_ms: start_ms = last_ms + 1

    if start_ms >= now_ms: 
        return df

    chunk_size = 1000 * {'1m':60,'5m':300,'15m':900,'1h':3600,'4h':14400,'1d':86400}.get(tf, 3600) * 1000
    ranges =[]
    curr = start_ms
    while curr < now_ms:
        nxt = min(curr + chunk_size, now_ms)
        ranges.append((symbol, tf, int(curr), int(nxt)))
        curr = nxt + 1

    all_data =[]
    # 15 concurrent threads for massive speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(fetch_chunk, *r) for r in ranges]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: all_data.extend(res)
            
    if all_data:
        new_df = pd.DataFrame(all_data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        new_df['timestamp'] = pd.to_datetime(new_df['time'], unit='ms')
        new_df[['open', 'high', 'low', 'close', 'volume']] = new_df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric, errors='coerce')
        new_df = new_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        if not df.empty:
            combined = pd.concat([df, new_df]).drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        else:
            combined = new_df.sort_values('timestamp').reset_index(drop=True)
            
        combined.to_parquet(file_path, engine='pyarrow')
        return combined
    return df
