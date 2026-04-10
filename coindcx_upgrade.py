import pandas as pd
import requests
import asyncio
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CoinDCXManager:
    def __init__(self):
        self.id = 'coindcx'
        self.public_url = "https://public.coindcx.com"
        self.stealth_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

    async def fetch_symbols(self):
        try:
            response = await asyncio.to_thread(requests.get, "https://api.coindcx.com/exchange/v1/markets_details", headers=self.stealth_headers, timeout=15, verify=False)
            if response.status_code != 200:
                response = await asyncio.to_thread(requests.get, "https://api.coindcx.com/exchange/ticker", headers=self.stealth_headers, timeout=15, verify=False)
            if response.status_code != 200: return ["BTCUSDT", "ETHUSDT"]

            symbols = [item.get('coindcx_name', item.get('market', '')) for item in response.json()]
            return sorted(list(set([s for s in symbols if s and ('USDT' in s or 'USD' in s)])))
        except Exception: return ["BTCUSDT", "ETHUSDT"]

    async def fetch_history(self, symbol, timeframe='1h', limit=3000):
        try:
            clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            fetch_limit = min(limit, 2000)
            
            # --- ATTEMPT 1: CoinDCX Native API ---
            url = f"{self.public_url}/market_data/candles"
            candidates = [clean_symbol]
            if clean_symbol.endswith('USDT'):
                base = clean_symbol[:-4]
                candidates.extend([f"B-{base}_USDT", f"B-{clean_symbol}", f"{base}_USDT", f"I-{base}_INR"])
            
            data = None
            for cand in candidates:
                params = {'pair': cand, 'interval': tf, 'limit': fetch_limit}
                response = await asyncio.to_thread(requests.get, url, params=params, headers=self.stealth_headers, verify=False)
                if response.status_code == 200:
                    resp_json = response.json()
                    if isinstance(resp_json, list) and len(resp_json) > 0:
                        data = resp_json
                        break
            
            if data and isinstance(data, list):
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                return df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True).dropna().tail(limit)
                
            # --- ATTEMPT 2: THE UNIVERSAL LIQUIDITY FALLBACK (Binance) ---
            print(f"⚠️ CoinDCX missing history for {symbol}. Falling back to Liquidity Provider...")
            b_params = {"symbol": clean_symbol, "interval": tf, "limit": min(limit, 1000)}
            
            # Try Binance Spot
            b_resp = await asyncio.to_thread(requests.get, "https://api.binance.com/api/v3/klines", params=b_params, timeout=10)
            if b_resp.status_code != 200:
                # Try Binance Futures
                b_resp = await asyncio.to_thread(requests.get, "https://fapi.binance.com/fapi/v1/klines", params=b_params, timeout=10)
                
            if b_resp.status_code == 200:
                b_data = b_resp.json()
                if b_data and len(b_data) > 0:
                    df = pd.DataFrame(b_data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
                    df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
                    cols = ['open', 'high', 'low', 'close', 'volume']
                    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                    return df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True).dropna().tail(limit)

            return pd.DataFrame()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
