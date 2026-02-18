import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna
from sqlalchemy.orm import Session
from . import models, database, security, crud

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def fetch_history(self, symbol):
        exchange = ccxt.delta({'options': {'defaultType': 'future'}})
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except: return None
        finally: await exchange.close()

    def get_indicator_value(self, df, config):
        type_ = config.get('type')
        params = config.get('params', {})
        
        # 1. RAW DATA
        if type_ in ['close', 'open', 'high', 'low', 'volume']:
            return df.iloc[-1][type_]
        if type_ == 'number':
            return float(params.get('value', 0))

        # 2. CALCULATE INDICATOR USING 'ta' LIBRARY
        # We construct the column name that 'ta' library generates automatically
        # e.g. RSI(14) -> 'momentum_rsi'
        # e.g. BB(20,2) -> 'volatility_bbh', 'volatility_bbl'
        
        try:
            # We add ALL indicators to the dataframe at once (simplest way to support 100+)
            # Note: In production, we would calculate specific ones for performance.
            df = add_all_ta_features(
                df, open="open", high="high", low="low", close="close", volume="volume", fillna=True
            )
            
            # MAPPING THE NAMES
            # This is a heuristic map. 'ta' library uses specific naming conventions.
            col_name = ""
            if type_ == 'rsi': col_name = 'momentum_rsi'
            elif type_ == 'ema': col_name = f"trend_ema_{params.get('length', 14)}"
            elif type_ == 'sma': col_name = f"trend_sma_{params.get('length', 14)}"
            elif type_ == 'macd': col_name = 'trend_macd'
            elif type_ == 'macd_diff': col_name = 'trend_macd_diff'
            elif type_ == 'adx': col_name = 'trend_adx'
            elif type_ == 'cci': col_name = 'trend_cci'
            elif type_ == 'atr': col_name = 'volatility_atr'
            elif type_ == 'bb_upper': col_name = 'volatility_bbh'
            elif type_ == 'bb_lower': col_name = 'volatility_bbl'
            
            # If we calculated it, return the last value
            if col_name in df.columns:
                return df.iloc[-1][col_name]
            
            # Fallback for dynamic EMAs/SMAs if 'add_all' missed specific lengths
            if type_ == 'ema': return df['close'].ewm(span=int(params.get('length', 14))).mean().iloc[-1]
            if type_ == 'sma': return df['close'].rolling(int(params.get('length', 14))).mean().iloc[-1]

            return 0.0
        except Exception as e:
            print(f"Indicator Error {type_}: {e}")
            return 0.0

    def check_conditions(self, df, logic):
        conditions = logic.get('conditions', [])
        if not conditions: return False

        for cond in conditions:
            # Calculate Left Side
            val_left = self.get_indicator_value(df, cond.get('left'))
            # Calculate Right Side
            val_right = self.get_indicator_value(df, cond.get('right'))
            
            op = cond.get('operator')

            if op == 'GREATER_THAN' and not (val_left > val_right): return False
            if op == 'LESS_THAN' and not (val_left < val_right): return False
            if op == 'EQUALS' and not (val_left == val_right): return False
            
            # For Crossover, we need previous values. 
            # For MVP, we simplify to GT/LT check on current candle.
            if op == 'CROSSES_ABOVE' and not (val_left > val_right): return False 
            if op == 'CROSSES_BELOW' and not (val_left < val_right): return False

        return True

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        df = await self.fetch_history(symbol)
        if df is None: return

        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol).all()

        for strat in strategies:
            if self.check_conditions(df, strat.logic_configuration):
                crud.create_log(db, strat.id, f"⚡ Condition Met! {symbol} @ {current_price}", "INFO")
                
                user = strat.owner
                if not user.delta_api_key: continue

                logic = strat.logic_configuration
                qty = logic.get('quantity', 1)
                params = {}
                if logic.get('sl', 0) > 0: params['stop_loss_price'] = current_price * (1 - (logic['sl']/100))
                if logic.get('tp', 0) > 0: params['take_profit_price'] = current_price * (1 + (logic['tp']/100))

                exchange = None
                try:
                    api_key = security.decrypt_value(user.delta_api_key)
                    secret = security.decrypt_value(user.delta_api_secret)
                    exchange = ccxt.delta({
                        'apiKey': api_key, 'secret': secret,
                        'options': { 'defaultType': 'future', 'adjustForTimeDifference': True },
                        'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange' }
                    })
                    
                    crud.create_log(db, strat.id, f"🚀 Buying {qty} contracts", "INFO")
                    await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                    crud.create_log(db, strat.id, f"✅ Order Filled!", "SUCCESS")
                except Exception as e:
                    crud.create_log(db, strat.id, f"❌ Failed: {str(e)[:50]}", "ERROR")
                finally:
                    if exchange: await exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ PRO ENGINE STARTED")
        while self.is_running:
            try:
                async with websockets.connect(self.delta_ws_url) as websocket:
                    db = database.SessionLocal()
                    symbols = await self.get_active_symbols(db)
                    db.close()
                    payload = { "type": "subscribe", "payload": { "channels": [{ "name": "v2/ticker", "symbols": symbols }] } }
                    await websocket.send(json.dumps(payload))
                    async for message in websocket:
                        if not self.is_running: break
                        data = json.loads(message)
                        if data.get('type') == 'v2/ticker':
                            try:
                                db_tick = database.SessionLocal()
                                await self.execute_trade(db_tick, data['symbol'], float(data['mark_price']))
                                db_tick.close()
                            except: pass
            except: await asyncio.sleep(5)

engine = RealTimeEngine()
