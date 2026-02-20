import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
from sqlalchemy.orm import Session
from . import models, database, security, crud

# PURE MATH - NO EXTERNAL TA LIBRARIES
class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols if symbols else ["BTCUSD"]

    async def fetch_history(self, symbol):
        exchange = ccxt.delta({'options': {'defaultType': 'future'}})
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            return df
        except: return None
        finally: await exchange.close()

    def check_conditions(self, df, logic):
        try:
            # 1. Prepare Data
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name, params = item.get('type'), item.get('params', {})
                    length = int(params.get('length') or 14)
                    col_name = f"{name}_{length}"
                    
                    if col_name in df.columns: continue

                    if name == 'rsi':
                        delta = df['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                        rs = gain / loss
                        df[col_name] = 100 - (100 / (1 + rs))
                    elif name == 'ema':
                        df[col_name] = df['close'].ewm(span=length, adjust=False).mean()
                    elif name == 'sma':
                        df[col_name] = df['close'].rolling(window=length).mean()

            # 2. Evaluate
            df = df.fillna(0)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # Helper
            def get_val(row, item):
                if item['type'] == 'number': return float(item['params']['value'])
                if item['type'] in ['close', 'open', 'high', 'low']: return row[item['type']]
                length = int(item['params'].get('length') or 14)
                return row.get(f"{item['type']}_{length}", 0)

            for cond in conditions:
                v_l, v_r = get_val(last_row, cond['left']), get_val(last_row, cond['right'])
                p_l, p_r = get_val(prev_row, cond['left']), get_val(prev_row, cond['right'])
                op = cond['operator']
                
                if op == 'GREATER_THAN' and not (v_l > v_r): return False
                if op == 'LESS_THAN' and not (v_l < v_r): return False
                if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): return False
                if op == 'CROSSES_BELOW' and not (val_left < val_right and prev_left >= prev_right): return False

            return True
        except: return False

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        df = await self.fetch_history(symbol)
        if df is None or df.empty: return

        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol).all()

        for strat in strategies:
            if self.check_conditions(df, strat.logic_configuration):
                crud.create_log(db, strat.id, f"⚡ Signal! {symbol} @ {current_price}", "INFO")
                
                user = strat.owner
                if not user.delta_api_key: continue

                logic, qty = strat.logic_configuration, float(logic.get('quantity', 1))
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
                    crud.create_log(db, strat.id, f"✅ Filled!", "SUCCESS")

                except Exception as e:
                    crud.create_log(db, strat.id, f"❌ Failed: {str(e)[:50]}", "ERROR")
                finally:
                    if exchange: await exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ PURE MATH ENGINE STARTED")
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
