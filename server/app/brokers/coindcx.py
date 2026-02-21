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
        """Fetches active Perpetual Futures from CoinDCX API"""
        print("... Connecting directly to CoinDCX API ...")
        try:
            response = await asyncio.to_thread(requests.get, f"{self.base_url}/exchange/v1/markets_details")
            markets = response.json()
            
            symbols = []
            for market in markets:
                name = market.get('coindcx_name', '')
                status = market.get('status')
                
                # STRICT FILTER: Active Futures starting with 'B-' and ending in '_USDT'
                if status == 'active' and name.startswith('B-') and name.endswith('_USDT'):
                    symbols.append(name)
            
            if not symbols:
                print("⚠️ Strict filter found no pairs. Using safe defaults.")
                symbols = ["B-BTC_USDT", "B-ETH_USDT", "B-XRP_USDT", "B-SOL_USDT", "B-DOGE_USDT"]
            else:
                unique_symbols = sorted(list(set(symbols)))
                print(f"✅ Loaded {len(unique_symbols)} Futures Pairs from CoinDCX")
                return unique_symbols
                
        except Exception as e:
            print(f"❌ CoinDCX Symbol Error: {e}")
            return ["B-BTC_USDT", "B-ETH_USDT"]

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        """Fetches candles directly from CoinDCX Public API"""
        try:
            # 1. AUTO-FIX THE SYMBOL FORMAT
            # If the user passed "BTC/USDT" or "BTC-USDT", we force it to the CoinDCX internal format "B-BTC_USDT"
            # This makes the backtester idiot-proof against old saved strategies.
            clean_symbol = symbol.replace("/", "").replace("-", "")
            if clean_symbol.endswith("USDT") and not clean_symbol.startswith("B-"):
                 # Extract base (e.g., BTC from BTCUSDT)
                 base = clean_symbol[:-4] 
                 internal_symbol = f"B-{base}_USDT"
                 print(f"🔄 Auto-corrected symbol {symbol} -> {internal_symbol}")
                 symbol = internal_symbol

            # Map timeframes to CoinDCX standards
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {
                'pair': symbol,
                'interval': tf,
                'limit': limit
            }
            
            print(f"📉 Fetching CoinDCX History: {symbol} on {tf}...")
            response = await asyncio.to_thread(requests.get, url, params=params)
            
            if response.status_code != 200:
                print(f"❌ CoinDCX API Rejected Request: {response.status_code} - {response.text}")
                return pd.DataFrame()

            data = response.json()
            
            if not data or not isinstance(data, list):
                print(f"❌ CoinDCX returned empty data for {symbol}")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            
            if 'time' not in df.columns:
                print(f"❌ Unexpected Data Format from CoinDCX: {df.columns}")
                return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            # CoinDCX sends newest to oldest. Reverse it!
            df = df.iloc[::-1].reset_index(drop=True)
            
            return df.dropna()
        except Exception as e:
            print(f"❌ CoinDCX Data Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
