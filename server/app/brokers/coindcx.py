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
        """Fetches directly from CoinDCX API"""
        print("... Connecting directly to CoinDCX API ...")
        try:
            # Run the synchronous request in an async thread to prevent blocking
            response = await asyncio.to_thread(requests.get, f"{self.base_url}/exchange/v1/markets_details")
            markets = response.json()
            
            symbols = []
            for market in markets:
                # Look for active USDT futures (CoinDCX usually prefixes these)
                if market.get('status') == 'active' and market.get('target_currency_short_name') == 'USDT':
                    name = market.get('coindcx_name', '')
                    if name: symbols.append(name)
            
            unique_symbols = sorted(list(set(symbols)))
            print(f"✅ Loaded {len(unique_symbols)} Pairs directly from CoinDCX")
            return unique_symbols
            
        except Exception as e:
            print(f"❌ CoinDCX Symbol Error: {e}")
            # Fallback to standard CoinDCX USDT names
            return ["B-BTC_USDT", "B-ETH_USDT", "B-XRP_USDT", "B-SOL_USDT"]

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        """Fetches candles directly from CoinDCX Public API"""
        try:
            # Map timeframes to CoinDCX standards
            # CoinDCX supports: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 1d
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {
                'pair': symbol,
                'interval': tf,
                'limit': limit
            }
            
            response = await asyncio.to_thread(requests.get, url, params=params)
            data = response.json()
            
            if not data or not isinstance(data, list):
                print(f"❌ CoinDCX returned empty data for {symbol}")
                return pd.DataFrame()
            
            # CoinDCX returns JSON list: [{'open':..., 'high':..., 'time':...}]
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            # CoinDCX sends newest to oldest. We must reverse it for backtesting!
            df = df.iloc[::-1].reset_index(drop=True)
            
            return df.dropna()
        except Exception as e:
            print(f"❌ CoinDCX Data Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
