import pandas as pd
import requests
import asyncio
import time

class CoinDCXManager:
    def __init__(self):
        self.id = 'coindcx'
        # Standard Public API URL
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"

    async def fetch_symbols(self):
        """Fetches ALL USDT pairs using the method verified by probe"""
        print("... Connecting to CoinDCX API for Symbols ...")
        try:
            # 1. Use the specific endpoint that worked in the probe
            url = f"{self.base_url}/exchange/v1/markets_details"
            
            # Run in thread to avoid blocking server
            response = await asyncio.to_thread(requests.get, url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ CoinDCX API Error: {response.status_code}")
                return []

            markets = response.json()
            
            symbols = []
            for market in markets:
                # 2. Simple Filter: Must be Active + USDT
                # We do NOT filter for 'B-' prefix anymore because user wants ALL pairs
                name = market.get('coindcx_name', '')
                status = market.get('status')
                
                if status == 'active' and 'USDT' in name:
                    symbols.append(name)
            
            # 3. Sort and Deduplicate
            unique_symbols = sorted(list(set(symbols)))
            
            if len(unique_symbols) > 5:
                print(f"✅ Loaded {len(unique_symbols)} Pairs from CoinDCX (e.g. {unique_symbols[0]})")
                return unique_symbols
            else:
                print("⚠️ CoinDCX returned too few symbols.")
                return []
                
        except Exception as e:
            print(f"❌ CoinDCX Symbol Exception: {e}")
            return [] # Return empty so Main.py keeps defaults if this fails

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        try:
            # Auto-clean symbol format (BTC/USDT -> BTCUSDT)
            clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
            
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {'pair': clean_symbol, 'interval': tf, 'limit': limit}
            
            response = await asyncio.to_thread(requests.get, url, params=params)
            data = response.json()
            
            if not data or not isinstance(data, list):
                # Retry with B- prefix (Futures convention)
                fallback = f"B-{clean_symbol}"
                params['pair'] = fallback
                response = await asyncio.to_thread(requests.get, url, params=params)
                data = response.json()
                
                if not data or not isinstance(data, list):
                    return pd.DataFrame()

            df = pd.DataFrame(data)
            if 'time' not in df.columns: return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            # Reverse to chronological order
            df = df.iloc[::-1].reset_index(drop=True)
            return df.dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
