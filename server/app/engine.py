import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from . import models, database, security, crud
import traceback

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols if symbols else ["BTC-USDT"]

    async def fetch_history(self, symbol, broker="DELTA", db=None, strat_ids=[]):
        exchange = None
        try:
            if broker == "COINDCX":
                exchange = ccxt.coindcx({'enableRateLimit': True})
            else:
                exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
                
            # CoinDCX requires strict timeframes. 1m is safe.
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            if not ohlcv: 
                if db:
                    for sid in strat_ids: crud.create_log(db, sid, f"❌ {broker} returned no history for {symbol}.", "ERROR")
                return pd.DataFrame()
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            return df.dropna()
            
        except Exception as e:
            if db:
                for sid in strat_ids: crud.create_log(db, sid, f"❌ History Fetch Error ({broker}): {str(e)}", "ERROR")
            return None
        finally: 
            if exchange: await exchange.close()

    def calculate_indicator(self, df, name, params):
        try:
            length = int(params.get('length') or 14)
            if name == 'rsi':
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))
            elif name == 'ema': return df['close'].ewm(span=length, adjust=False).mean()
            elif name == 'sma': return df['close'].rolling(window=length).mean()
            return pd.Series(0, index=df.index)
        except: return pd.Series(0, index=df.index)

    def check_conditions(self, df, logic):
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    name, params = item.get('type'), item.get('params', {})
                    length = int(params.get('length') or 14)
                    col_name = f"{name}_{length}"
                    if col_name not in df.columns:
                        df[col_name] = self.calculate_indicator(df, name, params)

            df = df.fillna(0)
            last_row, prev_row = df.iloc[-1], df.iloc[-2]

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
                if op == 'CROSSES_BELOW' and not (v_l < v_r and p_l >= p_r): return False
                if op == 'EQUALS' and not (v_l == v_r): return False
            return True
        except: return False

    async def execute_trade(self, db: Session, symbol: str, current_price: float, broker: str):
        strategies = db.query(models.Strategy).filter(
            models.Strategy.is_running == True, 
            models.Strategy.symbol == symbol,
            models.Strategy.broker == broker
        ).all()
        
        strat_ids = [s.id for s in strategies]
        if not strategies: return

        df = await self.fetch_history(symbol, broker, db, strat_ids)
        if df is None or df.empty: return

        for strat in strategies:
            # We add a heartbeat log so you know it's alive!
            crud.create_log(db, strat.id, f"📡 Ping: {symbol} @  | Checking logic...", "INFO")

            if self.check_conditions(df, strat.logic_configuration):
                user = strat.owner
                
                api_key_enc = user.coindcx_api_key if broker == "COINDCX" else user.delta_api_key
                secret_enc = user.coindcx_api_secret if broker == "COINDCX" else user.delta_api_secret

                if not api_key_enc:
                    crud.create_log(db, strat.id, f"❌ No API Keys found for {broker}. Go to Settings.", "ERROR")
                    continue

                logic = strat.logic_configuration
                qty = float(logic.get('quantity', 1))
                params = {}

                exchange = None
                try:
                    api_key = security.decrypt_value(api_key_enc)
                    secret = security.decrypt_value(secret_enc)
                    
                    if broker == "COINDCX":
                        exchange = ccxt.coindcx({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True})
                    else:
                        exchange = ccxt.delta({'apiKey': api_key, 'secret': secret, 'options': { 'defaultType': 'future', 'adjustForTimeDifference': True }, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange' }})
                    
                    crud.create_log(db, strat.id, f"🚀 Firing Order on {broker}: Buy {qty} {symbol}", "INFO")
                    order = await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                    crud.create_log(db, strat.id, f"✅ Order Filled! ID: {order.get('id', 'Confirmed')}", "SUCCESS")

                except ccxt.InsufficientFunds:
                    crud.create_log(db, strat.id, f"⚠️ Insufficient Margin to buy {qty} {symbol}.", "WARNING")
                except ccxt.AuthenticationError:
                    crud.create_log(db, strat.id, f"❌ Invalid API Keys for {broker}", "ERROR")
                except Exception as e:
                    crud.create_log(db, strat.id, f"❌ Trade Error: {str(e)[:100]}...", "ERROR")
                finally:
                    if exchange: await exchange.close()

    # --- WORLD 1: DELTA EXCHANGE LOOP ---
    async def run_delta_loop(self):
        print("🌐 Delta World Online.")
        while self.is_running:
            try:
                db = database.SessionLocal()
                strats = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.broker == "DELTA").all()
                symbols = list(set([s.symbol for s in strats]))
                db.close()
                
                if not symbols:
                    await asyncio.sleep(10)
                    continue

                async with websockets.connect(self.delta_ws_url) as websocket:
                    payload = { "type": "subscribe", "payload": { "channels": [{ "name": "v2/ticker", "symbols": symbols }] } }
                    await websocket.send(json.dumps(payload))
                    async for message in websocket:
                        if not self.is_running: break
                        data = json.loads(message)
                        if data.get('type') == 'v2/ticker':
                            try:
                                db_tick = database.SessionLocal()
                                await self.execute_trade(db_tick, data['symbol'], float(data['mark_price']), "DELTA")
                                db_tick.close()
                            except: pass
            except: await asyncio.sleep(5)

    # --- WORLD 2: COINDCX LOOP ---
    async def run_coindcx_loop(self):
        print("🌐 CoinDCX World Online.")
        exchange = ccxt.coindcx({'enableRateLimit': True})
        while self.is_running:
            try:
                db = database.SessionLocal()
                strats = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.broker == "COINDCX").all()
                symbols = list(set([s.symbol for s in strats]))
                
                for sym in symbols:
                    try:
                        # 1. Fetch current price
                        ticker = await exchange.fetch_ticker(sym)
                        current_price = float(ticker['last'])
                        
                        # 2. Execute logic
                        await self.execute_trade(db, sym, current_price, "COINDCX")
                        
                    except Exception as e:
                        # If fetching ticker fails, tell the user!
                        for s in [st for st in strats if st.symbol == sym]:
                            crud.create_log(db, s.id, f"❌ CoinDCX Connection Error for {sym}: {str(e)[:60]}", "ERROR")
                
                db.close()
            except Exception as e:
                pass
            
            # Check every 15 seconds to avoid rate limits
            await asyncio.sleep(15) 
            
        await exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ DUAL-CORE ENGINE STARTED")
        await asyncio.gather(
            self.run_delta_loop(),
            self.run_coindcx_loop()
        )

engine = RealTimeEngine()
