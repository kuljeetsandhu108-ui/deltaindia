import pandas as pd
import requests
import asyncio
import time

class CoinDCXManager:
    def __init__(self):
        self.id = 'coindcx'
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"

    async def fetch_symbols(self):
        """Fetches ALL USDT pairs using the Ticker API"""
        print("... CoinDCX Manager: Connecting to Ticker API ...")
        try:
            # 1. Use the Ticker endpoint (Proven to work)
            url = f"{self.base_url}/exchange/ticker"
            
            # Run in thread with a long timeout (30s)
            response = await asyncio.to_thread(requests.get, url, timeout=30)
            
            print(f"CoinDCX Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ CoinDCX API Error: {response.text}")
                return []

            data = response.json()
            
            symbols = []
            for item in data:
                pair = item.get('market', '')
                # STRICT FILTER: Must end in USDT
                if pair.endswith('USDT'):
                    symbols.append(pair)
            
            unique_symbols = sorted(list(set(symbols)))
            
            if len(unique_symbols) > 5:
                print(f"✅ CoinDCX Loaded {len(unique_symbols)} Pairs (e.g., {unique_symbols[0]})")
                return unique_symbols
            else:
                print("⚠️ CoinDCX returned 0 symbols in filter.")
                return []
                
        except Exception as e:
            print(f"❌ CoinDCX Exception: {e}")
            return [] 

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        try:
            # Clean Symbol: BTC/USDT -> BTCUSDT
            clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
            
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {'pair': clean_symbol, 'interval': tf, 'limit': limit}
            
            response = await asyncio.to_thread(requests.get, url, params=params)
            data = response.json()
            
            # If standard fails, try B- prefix (Futures)
            if not data or not isinstance(data, list):
                fallback = f"B-{clean_symbol}"
                params['pair'] = fallback
                response = await asyncio.to_thread(requests.get, url, params=params)
                data = response.json()
            
            if not data or not isinstance(data, list): return pd.DataFrame()

            df = pd.DataFrame(data)
            if 'time' not in df.columns: return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            # Reverse chronological
            df = df.iloc[::-1].reset_index(drop=True)
            return df.dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
