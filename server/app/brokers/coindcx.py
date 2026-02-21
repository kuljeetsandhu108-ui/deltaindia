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
        """Fetches all USDT pairs from CoinDCX (Spot & Futures)"""
        print("... Connecting directly to CoinDCX API ...")
        try:
            # We use the endpoint that we KNOW works from your probe
            response = await asyncio.to_thread(requests.get, f"{self.base_url}/exchange/v1/markets_details")
            markets = response.json()
            
            symbols = []
            for market in markets:
                # 1. Must be Active
                if market.get('status') != 'active': continue
                
                # 2. Must be a USDT pair
                name = market.get('coindcx_name', '')
                if 'USDT' in name:
                    symbols.append(name)
            
            if not symbols:
                print("⚠️ No symbols found even with loose filter.")
                return ["BTCUSDT", "ETHUSDT"] # Ultimate Fallback
            
            unique_symbols = sorted(list(set(symbols)))
            print(f"✅ Loaded {len(unique_symbols)} Pairs from CoinDCX")
            return unique_symbols
                
        except Exception as e:
            print(f"❌ CoinDCX Symbol Error: {e}")
            return ["BTCUSDT", "ETHUSDT"]

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        try:
            # Auto-Fix Symbol format: 
            # If user sends "BTC/USDT", CoinDCX wants "BTCUSDT" or "B-BTC_USDT"
            # Based on your logs, "PYTHUSDT" exists, so we try "BTCUSDT" style first.
            
            clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
            
            # Map timeframes
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {
                'pair': clean_symbol, # e.g. BTCUSDT
                'interval': tf,
                'limit': limit
            }
            
            print(f"📉 Fetching CoinDCX History: {clean_symbol} on {tf}...")
            response = await asyncio.to_thread(requests.get, url, params=params)
            
            data = response.json()
            
            # Handle empty response
            if not data or not isinstance(data, list):
                # RETRY STRATEGY: Try adding 'B-' prefix if normal failed (Some accounts use B-BTC_USDT)
                # This handles the specific Futures case if Spot fails
                fallback_symbol = f"B-{clean_symbol.replace('USDT', '_USDT')}"
                print(f"⚠️ Empty data for {clean_symbol}, trying {fallback_symbol}...")
                params['pair'] = fallback_symbol
                response = await asyncio.to_thread(requests.get, url, params=params)
                data = response.json()
                
                if not data or not isinstance(data, list):
                    print(f"❌ CoinDCX Data Failed.")
                    return pd.DataFrame()

            df = pd.DataFrame(data)
            
            if 'time' not in df.columns: return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            # Reverse to be chronological
            df = df.iloc[::-1].reset_index(drop=True)
            
            return df.dropna()
        except Exception as e:
            print(f"❌ CoinDCX Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
