import ccxt.async_support as ccxt
import pandas as pd
import asyncio

class CoinDCXManager:
    def __init__(self):
        self.id = 'coindcx'

    async def fetch_symbols(self):
        """Fetches all USDT pairs from CoinDCX"""
        print("... Connecting to CoinDCX ...")
        exchange = None
        try:
            exchange = ccxt.coindcx({'enableRateLimit': True})
            markets = await exchange.load_markets()
            
            symbols = []
            for symbol, market in markets.items():
                # Get active USDT pairs
                if market.get('active') and 'USDT' in symbol:
                    symbols.append(symbol)
            
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
            if timeframe == '1m': limit = 2000 
            
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
