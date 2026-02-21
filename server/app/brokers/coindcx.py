import pandas as pd
import requests
import asyncio
import time
import urllib3

# Disable SSL warnings to keep logs clean
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CoinDCXManager:
    def __init__(self):
        self.id = 'coindcx'
        self.public_url = "https://public.coindcx.com"

    async def fetch_symbols(self):
        """Fetches ALL USDT pairs using Ticker API with SSL Bypass"""
        print("... CoinDCX Manager: Fetching Symbols ...")
        try:
            # 1. Use Ticker API (Proven to work)
            url = "https://api.coindcx.com/exchange/ticker"
            
            # 2. DISABLE SSL VERIFICATION (The Fix)
            # We use verify=False because Docker containers sometimes have outdated certs
            response = await asyncio.to_thread(requests.get, url, timeout=15, verify=False)
            
            if response.status_code != 200:
                print(f"❌ CoinDCX API Status: {response.status_code}")
                return ["BTCUSDT", "ETHUSDT"]

            data = response.json()
            
            symbols = []
            for item in data:
                pair = item.get('market', '')
                # Filter for USDT
                if pair.endswith('USDT'):
                    symbols.append(pair)
            
            unique_symbols = sorted(list(set(symbols)))
            
            if len(unique_symbols) > 5:
                print(f"✅ CoinDCX Loaded {len(unique_symbols)} Pairs!")
                return unique_symbols
            else:
                print("⚠️ CoinDCX returned 0 symbols in filter.")
                return ["BTCUSDT", "ETHUSDT"]
                
        except Exception as e:
            # THIS PRINT IS CRITICAL
            print(f"❌ CRITICAL COINDCX ERROR: {str(e)}")
            return ["BTCUSDT", "ETHUSDT"]

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        try:
            clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
            
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {'pair': clean_symbol, 'interval': tf, 'limit': limit}
            
            # Disable SSL here too
            response = await asyncio.to_thread(requests.get, url, params=params, verify=False)
            data = response.json()
            
            if not data or not isinstance(data, list):
                # Retry with B- prefix
                fallback = f"B-{clean_symbol}"
                params['pair'] = fallback
                response = await asyncio.to_thread(requests.get, url, params=params, verify=False)
                data = response.json()
            
            if not data or not isinstance(data, list): return pd.DataFrame()

            df = pd.DataFrame(data)
            if 'time' not in df.columns: return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df.iloc[::-1].reset_index(drop=True).dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
