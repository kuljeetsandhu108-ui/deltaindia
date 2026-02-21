import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import time
import hmac
import hashlib
import requests
from sqlalchemy.orm import Session
from . import models, database, security, crud
from .brokers.coindcx import coindcx_manager

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session, broker="DELTA"):
        strategies = db.query(models.Strategy).filter(
            models.Strategy.is_running == True, 
            models.Strategy.broker == broker
        ).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols

    async def fetch_history(self, symbol, broker="DELTA"):
        exchange = None
        try:
            if broker == "COINDCX":
                return await coindcx_manager.fetch_history(symbol, timeframe='1m', limit=100)
            else:
                exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
                if not ohlcv: return pd.DataFrame()
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                return df.dropna()
        except: return None
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
                if item['type'] in ['close', 'open', 'high', 'low']: return float(row[item['type']])
                length = int(item['params'].get('length') or 14)
                return float(row.get(f"{item['type']}_{length}", 0))

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
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol, models.Strategy.broker == broker).all()
        if not strategies: return

        df = await self.fetch_history(symbol, broker)
        if df is None or df.empty: return

        for strat in strategies:
            # 📡 Ping to terminal so user knows the engine is actively monitoring this strategy
            crud.create_log(db, strat.id, f"📡 System Check: {symbol} @ ", "INFO")

            if self.check_conditions(df, strat.logic_configuration):
                user = strat.owner
                api_key_enc = user.coindcx_api_key if broker == "COINDCX" else user.delta_api_key
                secret_enc = user.coindcx_api_secret if broker == "COINDCX" else user.delta_api_secret

                if not api_key_enc:
                    crud.create_log(db, strat.id, f"❌ No API Keys saved for {broker}.", "ERROR")
                    continue

                logic = strat.logic_configuration
                qty = float(logic.get('quantity', 1))

                try:
                    api_key = security.decrypt_value(api_key_enc)
                    secret = security.decrypt_value(secret_enc)
                    
                    # --- DELTA EXCHANGE EXECUTION ---
                    if broker == "DELTA":
                        exchange = ccxt.delta({'apiKey': api_key, 'secret': secret, 'options': { 'defaultType': 'future', 'adjustForTimeDifference': True }, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange' }})
                        params = {}
                        if logic.get('sl', 0) > 0: params['stop_loss_price'] = current_price * (1 - (logic['sl']/100))
                        if logic.get('tp', 0) > 0: params['take_profit_price'] = current_price * (1 + (logic['tp']/100))
                        
                        crud.create_log(db, strat.id, f"🚀 Firing Order on DELTA: Buy {qty} {symbol}", "INFO")
                        order = await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                        crud.create_log(db, strat.id, f"✅ Order Filled! ID: {order.get('id')}", "SUCCESS")
                        await exchange.close()
                    
                    # --- COINDCX DIRECT API EXECUTION (Bypassing CCXT) ---
                    elif broker == "COINDCX":
                        crud.create_log(db, strat.id, f"🚀 Firing Order on COINDCX: Buy {qty} {symbol}", "INFO")
                        
                        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"
                        timestamp = int(time.time() * 1000)
                        
                        payload = {
                            "market": symbol,
                            "side": "buy",
                            "order_type": "market_order",
                            "total_quantity": qty,
                            "timestamp": timestamp
                        }
                        
                        # Generate HMAC SHA256 Signature for CoinDCX
                        json_payload = json.dumps(payload, separators=(',', ':'))
                        signature = hmac.new(bytes(secret, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
                        
                        headers = {
                            'Content-Type': 'application/json',
                            'X-AUTH-APIKEY': api_key,
                            'X-AUTH-SIGNATURE': signature
                        }
                        
                        response = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
                        res_data = response.json()
                        
                        if response.status_code == 200:
                            crud.create_log(db, strat.id, f"✅ Order Filled! ID: {res_data.get('id', 'Confirmed')}", "SUCCESS")
                        else:
                            err_msg = res_data.get('message', str(res_data))
                            if "margin" in err_msg.lower() or "balance" in err_msg.lower():
                                crud.create_log(db, strat.id, f"⚠️ Insufficient Margin: {err_msg}", "WARNING")
                            else:
                                crud.create_log(db, strat.id, f"❌ Order Failed: {err_msg}", "ERROR")

                except ccxt.InsufficientFunds:
                    crud.create_log(db, strat.id, f"⚠️ Insufficient Margin on Delta.", "WARNING")
                except ccxt.AuthenticationError:
                    crud.create_log(db, strat.id, f"❌ Invalid API Keys for {broker}", "ERROR")
                except Exception as e:
                    crud.create_log(db, strat.id, f"❌ Execution Error: {str(e)[:50]}", "ERROR")

    # --- CORE 1: DELTA ---
    async def run_delta_loop(self):
        print("🌐 Delta World Online.")
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "DELTA")
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

    # --- CORE 2: COINDCX ---
    async def run_coindcx_loop(self):
        print("🌐 CoinDCX World Online.")
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "COINDCX")
                
                # Fetch recent history to get current price and evaluate logic
                for sym in symbols:
                    try:
                        df = await coindcx_manager.fetch_history(sym, '1m', 5)
                        if not df.empty:
                            current_price = df.iloc[-1]['close']
                            await self.execute_trade(db, sym, current_price, "COINDCX")
                    except Exception as e:
                        print(f"CoinDCX Engine Error: {e}")
                
                db.close()
            except: pass
            
            # Run this loop every 15 seconds so we don't hit CoinDCX rate limits
            await asyncio.sleep(15)

    async def start(self):
        self.is_running = True
        print("✅ DUAL-CORE ENGINE STARTED")
        await asyncio.gather(self.run_delta_loop(), self.run_coindcx_loop())

engine = RealTimeEngine()
