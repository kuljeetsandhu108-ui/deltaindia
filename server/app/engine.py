import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
import pandas_ta as ta
from sqlalchemy.orm import Session
from . import models, database, security, crud

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"
        # Cache candles to avoid fetching history on every tick
        self.market_data = {} 

    async def fetch_history(self, symbol):
        # Fetch last 100 candles for calculation
        exchange = ccxt.delta({'options': {'defaultType': 'future'}})
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except: return None
        finally: await exchange.close()

    def check_conditions(self, df, logic):
        # 1. Calculate Indicators
        # Example: Calculate RSI 14
        df['rsi'] = df.ta.rsi(length=14)
        df['ema_20'] = df.ta.ema(length=20)
        df['ema_50'] = df.ta.ema(length=50)

        # Get latest values
        last_row = df.iloc[-1]
        
        conditions = logic.get('conditions', [])
        if not conditions: return False

        # 2. Evaluate User Logic
        # For MVP, we handle: RSI < Value, and EMA Cross
        for cond in conditions:
            indicator = cond.get('indicator', '').upper()
            operator = cond.get('operator', '')
            value = float(cond.get('value', 0))

            if indicator == 'RSI':
                current_rsi = last_row['rsi']
                if operator == 'LESS_THAN' and not (current_rsi < value): return False
                if operator == 'GREATER_THAN' and not (current_rsi > value): return False
            
            # Add more indicators here later...

        return True # All conditions passed

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        # 1. Fetch History for Math
        df = await self.fetch_history(symbol)
        if df is None: return

        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol).all()

        for strat in strategies:
            # 2. CHECK LOGIC
            should_trade = self.check_conditions(df, strat.logic_configuration)
            
            if not should_trade:
                # Log heartbeat occasionally? No, too noisy.
                continue

            # IF LOGIC PASSES -> EXECUTE
            crud.create_log(db, strat.id, f"⚡ Signal Detected! {symbol} @ {current_price}", "INFO")
            
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
                
                crud.create_log(db, strat.id, f"🚀 Firing Order: Buy {qty}", "INFO")
                await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                crud.create_log(db, strat.id, f"✅ Order Filled!", "SUCCESS")

            except Exception as e:
                msg = str(e)
                if "insufficient_margin" in msg: crud.create_log(db, strat.id, "❌ No Money in Wallet", "ERROR")
                elif "invalid_api_key" in msg: crud.create_log(db, strat.id, "❌ Auth Failed", "ERROR")
                else: crud.create_log(db, strat.id, f"❌ Error: {msg[:50]}", "ERROR")
            finally:
                if exchange: await exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ SMART ENGINE STARTED")
        while self.is_running:
            try:
                async with websockets.connect(self.delta_ws_url) as websocket:
                    print("🔗 Connected")
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
            except Exception as e:
                print(f"WS Error: {e}")
                await asyncio.sleep(5)

engine = RealTimeEngine()
