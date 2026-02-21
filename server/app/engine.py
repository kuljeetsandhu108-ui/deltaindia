import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
from sqlalchemy.orm import Session
from . import models, database, security, crud

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols if symbols else ["BTC-USDT"]

    async def fetch_history(self, symbol, broker="DELTA"):
        exchange = None
        try:
            if broker == "COINDCX":
                exchange = ccxt.coindcx({'enableRateLimit': True})
            else:
                exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
                
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            return df
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
            elif name == 'ema':
                return df['close'].ewm(span=length, adjust=False).mean()
            elif name == 'sma':
                return df['close'].rolling(window=length).mean()
            elif name == 'bb_upper':
                std_dev = float(params.get('std') or 2.0)
                sma = df['close'].rolling(window=length).mean()
                std = df['close'].rolling(window=length).std()
                return sma + (std * std_dev)
            elif name == 'bb_lower':
                std_dev = float(params.get('std') or 2.0)
                sma = df['close'].rolling(window=length).mean()
                std = df['close'].rolling(window=length).std()
                return sma - (std * std_dev)
            return pd.Series(0, index=df.index)
        except:
            return pd.Series(0, index=df.index)

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

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol).all()

        for strat in strategies:
            # 1. Fetch data from the specific broker
            df = await self.fetch_history(symbol, strat.broker)
            if df is None or df.empty: continue

            # 2. Check Logic
            if self.check_conditions(df, strat.logic_configuration):
                user = strat.owner
                
                # 3. Retrieve proper API keys based on Broker
                if strat.broker == "COINDCX":
                    api_key_enc = user.coindcx_api_key
                    secret_enc = user.coindcx_api_secret
                else:
                    api_key_enc = user.delta_api_key
                    secret_enc = user.delta_api_secret

                if not api_key_enc:
                    crud.create_log(db, strat.id, f"❌ No API Keys found for {strat.broker}", "ERROR")
                    continue

                logic = strat.logic_configuration
                qty = float(logic.get('quantity', 1))
                
                # Setup Stop Loss & Take Profit params
                params = {}
                if logic.get('sl', 0) > 0: params['stopLossPrice'] = current_price * (1 - (logic['sl']/100))
                if logic.get('tp', 0) > 0: params['takeProfitPrice'] = current_price * (1 + (logic['tp']/100))

                exchange = None
                try:
                    # Decrypt Keys
                    api_key = security.decrypt_value(api_key_enc)
                    secret = security.decrypt_value(secret_enc)
                    
                    # Connect to Specific Broker
                    if strat.broker == "COINDCX":
                        exchange = ccxt.coindcx({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True})
                    else:
                        exchange = ccxt.delta({
                            'apiKey': api_key, 'secret': secret,
                            'options': { 'defaultType': 'future', 'adjustForTimeDifference': True },
                            'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange' }
                        })
                    
                    crud.create_log(db, strat.id, f"🚀 Firing Order on {strat.broker}: Buy {qty} {symbol}", "INFO")
                    
                    # THE REAL TRADE COMMAND
                    order = await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                    
                    crud.create_log(db, strat.id, f"✅ Order Filled! ID: {order.get('id', 'Confirmed')}", "SUCCESS")

                # --- 🛡️ PROFESSIONAL ERROR HANDLING ---
                except ccxt.InsufficientFunds:
                    # THIS IS KEY: It catches the margin error specifically and logs it as a WARNING without crashing.
                    crud.create_log(db, strat.id, f"⚠️ Insufficient Margin to buy {qty} {symbol}. Trade skipped.", "WARNING")
                
                except ccxt.AuthenticationError:
                    crud.create_log(db, strat.id, f"❌ Invalid or Expired API Keys for {strat.broker}", "ERROR")
                
                except ccxt.NetworkError:
                    crud.create_log(db, strat.id, f"⚠️ Network Timeout. Broker didn't respond in time.", "WARNING")
                
                except Exception as e:
                    # Catch-all for weird errors
                    crud.create_log(db, strat.id, f"❌ Trade Error: {str(e)[:80]}...", "ERROR")
                finally:
                    if exchange: await exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ LIVE EXECUTION ENGINE STARTED")
        while self.is_running:
            try:
                # We use Delta Socket as the universal "Heartbeat" for price action
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
