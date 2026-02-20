import ccxt.async_support as ccxt
import pandas as pd
import asyncio

class CoinDCXManager:
    def __init__(self):
        # We use the standard CCXT CoinDCX driver
        self.id = 'coindcx'

    async def fetch_symbols(self):
        """Fetches all USDT pairs from CoinDCX"""
        print("... Connecting to CoinDCX ...")
        exchange = None
        try:
            exchange = ccxt.coindcx({'enableRateLimit': True})
            markets = await exchange.load_markets()
            
            # CoinDCX usually has pairs like 'BTC/USDT'
            symbols = []
            for symbol, market in markets.items():
                if market.get('active') and 'USDT' in symbol:
                    # We store the ID because CoinDCX API needs the raw ID (e.g. B-BTC_USDT)
                    # CCXT maps this automatically, but we prefer the symbol for UI
                    symbols.append(symbol)
            
            # Remove duplicates and sort
            unique_symbols = sorted(list(set(symbols)))
            print(f"✅ Loaded {len(unique_symbols)} Pairs from CoinDCX")
            return unique_symbols
            
        except Exception as e:
            print(f"❌ CoinDCX Symbol Error: {e}")
            return ["BTC/USDT", "ETH/USDT"] # Fallback
        finally:
            if exchange: await exchange.close()

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        """Fetches candles for Backtesting"""
        exchange = None
        try:
            exchange = ccxt.coindcx({'enableRateLimit': True})
            
            # Map timeframes to CoinDCX standards
            # CoinDCX supports: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 1d, 3d, 1w, 1M
            
            if timeframe == '1m': limit = 2000 # Deep fetch
            
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df.dropna()
        except Exception as e:
            print(f"❌ CoinDCX Data Error: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

coindcx_manager = CoinDCXManager()
