import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from sqlalchemy.orm import Session
from . import models, database, security, crud

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols if symbols else ["BTCUSD"]

    async def fetch_history(self, symbol):
        # Fetch candle history for math
        exchange = ccxt.delta({'options': {'defaultType': 'future'}})
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except: return None
        finally: await exchange.close()

    def check_conditions(self, df, logic):
        # 1. CALCULATE INDICATORS (Using 'ta' library)
        # RSI 14
        rsi_ind = RSIIndicator(close=df['close'], window=14)
        df['rsi'] = rsi_ind.rsi()
        
        # EMA 20 & 50
        ema_20_ind = EMAIndicator(close=df['close'], window=20)
        df['ema_20'] = ema_20_ind.ema_indicator()
        
        ema_50_ind = EMAIndicator(close=df['close'], window=50)
        df['ema_50'] = ema_50_ind.ema_indicator()

        # Get latest values
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] # Previous candle (for crossover checks)
        
        conditions = logic.get('conditions', [])
        if not conditions: return False

        for cond in conditions:
            indicator = cond.get('indicator', '').upper()
            operator = cond.get('operator', '')
            value = float(cond.get('value', 0))

            # --- RSI LOGIC ---
            if indicator == 'RSI':
                current_rsi = last_row['rsi']
                if operator == 'LESS_THAN' and not (current_rsi < value): return False
                if operator == 'GREATER_THAN' and not (current_rsi > value): return False

            # --- EMA CROSSOVER LOGIC ---
            if indicator == 'EMA':
                # Example: If user says "EMA 20 CROSSES_ABOVE EMA 50"
                # We interpret this as: EMA20 was below 50, now is above 50.
                if operator == 'CROSSES_ABOVE':
                    # Check if EMA20 crossed UP
                    now_above = last_row['ema_20'] > last_row['ema_50']
                    prev_below = prev_row['ema_20'] <= prev_row['ema_50']
                    if not (now_above and prev_below): return False

        return True # All conditions passed

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        # Fetch Data
        df = await self.fetch_history(symbol)
        if df is None: return

        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol).all()

        for strat in strategies:
            # CHECK LOGIC
            should_trade = self.check_conditions(df, strat.logic_configuration)
            
            if not should_trade: continue # Skip if conditions not met

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
