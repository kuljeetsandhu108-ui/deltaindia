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
from sqlalchemy.orm.attributes import flag_modified
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
        return list(set([s.symbol for s in strategies]))

    async def fetch_history(self, symbol, broker="DELTA"):
        exchange = None
        try:
            if broker == "COINDCX":
                return await coindcx_manager.fetch_history(symbol, timeframe='1m', limit=100)
            else:
                exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
                hist_symbol = symbol.replace('-', '') if 'USDT' not in symbol else symbol
                ohlcv = await exchange.fetch_ohlcv(hist_symbol, timeframe='1m', limit=100)
                if not ohlcv: return pd.DataFrame()
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                return df.dropna()
        except: return None
        finally: 
            if exchange: await exchange.close()


        
        first_valid = np.argmax(valid_mask)
        start_idx = first_valid + length - 1
        if start_idx >= len(vals): return pd.Series(ema, index=series.index)
        
        # TradingView starts the EMA with an SMA baseline
        ema[start_idx] = np.mean(vals[first_valid : start_idx + 1])
        
        # TradingView strict compounding loop
        for i in range(start_idx + 1, len(vals)):
            if np.isnan(vals[i]):
                ema[i] = ema[i-1]
            else:
                ema[i] = alpha * vals[i] + (1 - alpha) * ema[i - 1]
        return pd.Series(ema, index=series.index)

    def calculate_indicator(self, df, name, params):
        import pandas as pd
        import numpy as np
        try:
            length = int(params.get('length') or 14)
            if name == 'rsi':
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                return 100 - (100 / (1 + (gain / loss)))
            elif name == 'ema': return self.calc_tv_ema(df['close'], length)
            elif name == 'sma': return df['close'].rolling(window=length).mean()
            elif name == 'macd':
                f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                return self.calc_tv_ema(df['close'], f) - self.calc_tv_ema(df['close'], s)
            elif name == 'bb_upper':
                std = float(params.get('std', 2.0))
                return df['close'].rolling(window=length).mean() + (df['close'].rolling(window=length).std() * std)
            elif name == 'bb_lower':
                std = float(params.get('std', 2.0))
                return df['close'].rolling(window=length).mean() - (df['close'].rolling(window=length).std() * std)
            elif name == 'atr':
                tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                return tr.rolling(window=length).mean()
            elif name == 'vwap':
                tp = (df['high'] + df['low'] + df['close']) / 3
                return (tp * df['volume']).rolling(window=length).sum() / df['volume'].rolling(window=length).sum()
            elif name == 'donchian_upper': return df['high'].rolling(window=length).max()
            elif name == 'donchian_lower': return df['low'].rolling(window=length).min()
            elif name == 'keltner_upper' or name == 'keltner_lower':
                mult = float(params.get('multiplier', 2.0))
                mid = self.calc_tv_ema(df['close'], length)
                tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(window=length).mean()
                if name == 'keltner_upper': return mid + (mult * atr)
                else: return mid - (mult * atr)
            elif name == 'supertrend':
                mult = float(params.get('multiplier', 3.0))
                hl2 = (df['high'] + df['low']) / 2
                tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(window=length).mean().values
                c_val, u_val, l_val = df['close'].values, (hl2 + mult * atr).values, (hl2 - mult * atr).values
                st = np.zeros(len(c_val))
                in_up = True
                for i in range(1, len(c_val)):
                    if c_val[i] > u_val[i-1]: in_up = True
                    elif c_val[i] < l_val[i-1]: in_up = False
                    else:
                        if in_up and l_val[i] < l_val[i-1]: l_val[i] = l_val[i-1]
                        if not in_up and u_val[i] > u_val[i-1]: u_val[i] = u_val[i-1]
                    st[i] = l_val[i] if in_up else u_val[i]
                return pd.Series(st, index=df.index)
            elif name == 'psar':
                step, max_step = float(params.get('step', 0.02)), float(params.get('max_step', 0.2))
                h_val, l_val = df['high'].values, df['low'].values
                psar = np.zeros(len(h_val))
                bull = True
                af = step
                hp, lp, ep = h_val[0], l_val[0], h_val[0]
                psar[0] = l_val[0]
                for i in range(1, len(h_val)):
                    psar[i] = psar[i-1] + af * (ep - psar[i-1])
                    if bull:
                        if l_val[i] < psar[i]: bull, psar[i], af, ep, lp = False, hp, step, l_val[i], l_val[i]
                        else:
                            if h_val[i] > hp: hp, ep, af = h_val[i], h_val[i], min(af + step, max_step)
                            if i > 1 and l_val[i-1] < psar[i]: psar[i] = l_val[i-1]
                            if i > 2 and l_val[i-2] < psar[i]: psar[i] = l_val[i-2]
                    else:
                        if h_val[i] > psar[i]: bull, psar[i], af, ep, hp = True, lp, step, h_val[i], h_val[i]
                        else:
                            if l_val[i] < lp: lp, ep, af = l_val[i], l_val[i], min(af + step, max_step)
                            if i > 1 and h_val[i-1] > psar[i]: psar[i] = h_val[i-1]
                            if i > 2 and h_val[i-2] > psar[i]: psar[i] = h_val[i-2]
                return pd.Series(psar, index=df.index)
            elif name == 'aroon_up': return df['high'].rolling(window=length+1).apply(lambda x: 100 * np.argmax(x) / length, raw=True)
            elif name == 'aroon_down': return df['low'].rolling(window=length+1).apply(lambda x: 100 * np.argmin(x) / length, raw=True)
            elif name == 'williams_r':
                hh = df['high'].rolling(window=length).max()
                ll = df['low'].rolling(window=length).min()
                return (hh - df['close']) / (hh - ll) * -100
            elif name == 'mom': return df['close'] - df['close'].shift(length)
            elif name == 'hma':
                half_l, sqrt_l = int(length / 2), int(np.sqrt(length))
                def wma(s, l):
                    weights = np.arange(1, l + 1)
                    return s.rolling(l).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
                diff = 2 * wma(df['close'], half_l) - wma(df['close'], length)
                return wma(diff, sqrt_l)
            elif name == 'tsi':
                long_l, short_l = int(params.get('long_length', 25)), int(params.get('short_length', 13))
                diff = df['close'].diff()
                num = self.calc_tv_ema(self.calc_tv_ema(diff, long_l), short_l)
                den = self.calc_tv_ema(self.calc_tv_ema(diff.abs(), long_l), short_l)
                return 100 * (num / den)
            elif name == 'uo':
                fast, mid, slow = int(params.get('fast', 7)), int(params.get('mid', 14)), int(params.get('slow', 28))
                prev_close = df['close'].shift(1)
                bp = df['close'] - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                tr = pd.concat([df['high'], prev_close], axis=1).max(axis=1) - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                a1 = bp.rolling(fast).sum() / tr.rolling(fast).sum()
                a2 = bp.rolling(mid).sum() / tr.rolling(mid).sum()
                a3 = bp.rolling(slow).sum() / tr.rolling(slow).sum()
                return 100 * (4 * a1 + 2 * a2 + a3) / 7
            return pd.Series(0, index=df.index)
        except Exception as e:
            print(f"Indicator Math Error: {e}")
            return pd.Series(0, index=df.index)

    async def check_conditions(self, symbol, broker, current_price, logic):
        try:
            conditions = logic.get('conditions', [])
            if not conditions: return False
            
            df = await self.fetch_history(symbol, broker)
            if df is None or df.empty: return False
            
            # Inject current live price into the last row for real-time awareness
            df.loc[df.index[-1], 'close'] = current_price
            df = self.calculate_indicator(df, 'all_needed', logic) # Internal helper logic
            
            # Prepare Indicators
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    name, params = item.get('type'), item.get('params', {})
                    length = int(params.get('length') or 14)
                    col_name = f"{name}_{length}"
                    if col_name not in df.columns:
                        df[col_name] = self.calculate_indicator(df, name, params)

            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            has_event = False
            event_triggered = False
            all_states_true = True
            eps = 0.00000001

            def get_v(row, item):
                if item['type'] == 'number': return float(item['params']['value'])
                if item['type'] in ['close', 'open', 'high', 'low']: return float(row[item['type']])
                return float(row.get(f"{item['type']}_{int(item['params'].get('length', 14))}", 0))

            for cond in conditions:
                v_l, v_r = get_v(last, cond['left']), get_v(last, cond['right'])
                p_l, p_r = get_v(prev, cond['left']), get_v(prev, cond['right'])
                op = cond['operator']
                
                if op == 'CROSSES_ABOVE':
                    has_event = True
                    if (v_l > v_r + eps) and (p_l <= p_r + eps): event_triggered = True
                elif op == 'CROSSES_BELOW':
                    has_event = True
                    if (v_l < v_r - eps) and (p_l >= p_r - eps): event_triggered = True
                elif op == 'GREATER_THAN':
                    if not (v_l > v_r + eps): all_states_true = False
                elif op == 'LESS_THAN':
                    if not (v_l < v_r - eps): all_states_true = False
                elif op == 'EQUALS':
                    if not (abs(v_l - v_r) < eps): all_states_true = False

            if has_event:
                return event_triggered and all_states_true
            return all_states_true
        except: return False

    async def fire_order(self, db, strat_id, broker, symbol, side, qty, api_key_enc, secret_enc, price, reason, trade_mode="LIVE"):
        try:
            if trade_mode == 'PAPER':
                crud.create_log(db, strat_id, f"📄 PAPER TRADE: {reason} {side} {qty} {symbol} @ ${price}", "SUCCESS")
                return True
            api_key = security.decrypt_value(api_key_enc)
            secret = security.decrypt_value(secret_enc)
            
            if broker == "DELTA":
                exchange = ccxt.delta({'apiKey': api_key, 'secret': secret, 'options': { 'defaultType': 'future' }, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}})
                order = await exchange.create_order(symbol, 'market', side.lower(), qty)
                crud.create_log(db, strat_id, f"✅ {reason} {side} Filled! ID: {order.get('id')} @ ${price}", "SUCCESS")
                await exchange.close()
                return True
            
            elif broker == "COINDCX":
                cdcx_sym = symbol
                clean_sym = symbol.replace("/", "").replace("-", "")
                if clean_sym.endswith("USDT") and not clean_sym.startswith("B-"): cdcx_sym = f"B-{clean_sym[:-4]}_USDT"
                
                url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"
                payload = {"market": cdcx_sym, "side": side.lower(), "order_type": "market_order", "total_quantity": qty, "timestamp": int(time.time() * 1000)}
                json_payload = json.dumps(payload, separators=(',', ':'))
                signature = hmac.new(bytes(secret, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
                headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': api_key, 'X-AUTH-SIGNATURE': signature}
                
                response = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
                res_data = response.json()
                
                if response.status_code == 200:
                    crud.create_log(db, strat_id, f"✅ {reason} {side} Filled! ID: {res_data.get('id')} @ ${price}", "SUCCESS")
                    return True
                else:
                    crud.create_log(db, strat_id, f"❌ Order Failed: {res_data.get('message', str(res_data))}", "ERROR")
                    return False
        except Exception as e:
            crud.create_log(db, strat_id, f"❌ Engine Error: {str(e)[:50]}", "ERROR")
            return False


    async def get_balance(self, broker, api_key_enc, secret_enc):
        try:
            api_key = security.decrypt_value(api_key_enc)
            secret = security.decrypt_value(secret_enc)
            if broker == "DELTA":
                exchange = ccxt.delta({'apiKey': api_key, 'secret': secret, 'options': { 'defaultType': 'future' }, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}})
                bal = await exchange.fetch_balance()
                await exchange.close()
                return max(float(bal.get('USDT', {}).get('free', 0)), float(bal.get('USD', {}).get('free', 0)))
            elif broker == "COINDCX":
                url = "https://api.coindcx.com/exchange/v1/users/balances"
                payload = {"timestamp": int(time.time() * 1000)}
                json_payload = json.dumps(payload, separators=(',', ':'))
                signature = hmac.new(bytes(secret, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
                headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': api_key, 'X-AUTH-SIGNATURE': signature}
                resp = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
                if resp.status_code == 200:
                    balances = resp.json()
                    for b in balances:
                        if b.get('currency') == 'USDT': return float(b.get('balance', 0))
            return 0.0
        except Exception as err:
            print(f"Balance Fetch Error: {err}")
            return 0.0

    async def execute_trade(self, db: Session, symbol: str, current_price: float, broker: str):
        if current_price <= 0: return

        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True, models.Strategy.symbol == symbol, models.Strategy.broker == broker).all()

        for strat in strategies:
            logic = strat.logic_configuration or {}
            state = logic.get('state', 'WAITING')
            side = logic.get('side', 'BUY').upper()
            trade_mode = logic.get('tradeMode', 'PAPER').upper()
            wallet_pct = float(logic.get('walletPct', 10))
            leverage = float(logic.get('leverage', 1))
            trade_mode = logic.get('tradeMode', 'PAPER').upper()

            user = strat.owner
            api_key_enc = user.coindcx_api_key if broker == "COINDCX" else user.delta_api_key
            secret_enc = user.coindcx_api_secret if broker == "COINDCX" else user.delta_api_secret

            if state == 'WAITING':
                is_trigger = await self.check_conditions(symbol, broker, current_price, logic)
                if is_trigger:
                    if not api_key_enc:
                        crud.create_log(db, strat.id, f"❌ No API Keys saved for {broker}.", "ERROR")
                        continue
                    
                    if trade_mode == 'LIVE':
                        balance = await self.get_balance(broker, api_key_enc, secret_enc)
                    else:
                        balance = 1000.0 # Paper trade default balance
                    
                    if balance <= 0:
                        crud.create_log(db, strat.id, f"❌ Insufficient Balance (Available: ${balance}). Auto-pausing strategy.", "ERROR")
                        strat.is_running = False
                        db.commit()
                        continue

                    trade_value = balance * (wallet_pct / 100.0) * leverage
                    qty = round(trade_value / current_price, 4)
                    if qty <= 0:
                        crud.create_log(db, strat.id, f"❌ Trade Qty is 0 (Balance too low). Auto-pausing.", "ERROR")
                        strat.is_running = False
                        db.commit()
                        continue

                    crud.create_log(db, strat.id, f"🚀 ENTRY {side} {symbol} | Lev: {leverage}x | Qty: {qty}", "INFO")
                    success = await self.fire_order(db, strat.id, broker, symbol, side, qty, api_key_enc, secret_enc, current_price, "ENTRY", trade_mode)
                    
                    if success:
                        logic['state'] = 'IN_POSITION'
                        logic['entry_price'] = current_price
                        logic['entry_qty'] = qty
                        strat.logic_configuration = logic
                        flag_modified(strat, "logic_configuration")
                        db.commit()
                    else:
                        strat.is_running = False
                        db.commit()

            elif state == 'IN_POSITION':
                entry_price = float(logic.get('entry_price', current_price))
                sl_pct = float(logic.get('sl', 0))
                tp_pct = float(logic.get('tp', 0))

                exit_triggered, reason = False, ""
                
                # Logic to determine if SL or TP is hit based on Long/Short
                if side == 'BUY':
                    if sl_pct > 0 and current_price <= entry_price * (1 - (sl_pct/100)): exit_triggered, reason = True, "Stop Loss"
                    elif tp_pct > 0 and current_price >= entry_price * (1 + (tp_pct/100)): exit_triggered, reason = True, "Take Profit"
                else: # SELL (Short)
                    if sl_pct > 0 and current_price >= entry_price * (1 + (sl_pct/100)): exit_triggered, reason = True, "Stop Loss"
                    elif tp_pct > 0 and current_price <= entry_price * (1 - (tp_pct/100)): exit_triggered, reason = True, "Take Profit"

                if exit_triggered:
                    exit_side = 'SELL' if side == 'BUY' else 'BUY'
                    qty = float(logic.get('entry_qty', 1))
                    crud.create_log(db, strat.id, f"🏁 EXIT {reason} hit. Firing {exit_side} {qty}...", "INFO")
                    success = await self.fire_order(db, strat.id, broker, symbol, exit_side, qty, api_key_enc, secret_enc, current_price, f"EXIT ({reason})", trade_mode)
                    
                    if success:
                        logic['state'] = 'WAITING'
                        logic['entry_price'] = 0
                        strat.logic_configuration = logic
                        flag_modified(strat, "logic_configuration")
                        db.commit()
                    else:
                        strat.is_running = False
                        db.commit()

    async def run_delta_loop(self):
        print("🌐 Delta World Online (REST Polling).")
        import urllib3
        urllib3.disable_warnings()
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "DELTA")
                db.close()
                if symbols:
                    resp = await asyncio.to_thread(requests.get, "https://api.india.delta.exchange/v2/tickers", verify=False, timeout=10)
                    if resp.status_code == 200:
                        tickers = resp.json().get('result', [])
                        ticker_map = {}
                        for t in tickers:
                            val = t.get('close') or t.get('mark_price') or 0
                            ticker_map[t['symbol']] = float(val)
                        
                        for sym in symbols:
                            current_price = ticker_map.get(sym, 0.0)
                            if current_price > 0:
                                db_tick = database.SessionLocal()
                                await self.execute_trade(db_tick, sym, current_price, "DELTA")
                                db_tick.close()
            except Exception as err: pass
            await asyncio.sleep(2) # Safely check prices every 2 seconds

    async def run_coindcx_loop(self):
        print("🌐 CoinDCX World Online.")
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "COINDCX")
                db.close()
                if symbols:
                    resp = await asyncio.to_thread(requests.get, "https://api.coindcx.com/exchange/ticker", timeout=10)
                    ticker_map = {t['market']: float(t.get('last_price', 0)) for t in resp.json()}
                    for sym in symbols:
                        clean_sym = sym.replace('/', '').replace('-', '')
                        base = clean_sym.replace('USDT', '').replace('USD', '')
                        target_spot, target_future = f"{base}USDT", f"B-{base}_USDT"
                        current_price = ticker_map.get(target_future) or ticker_map.get(target_spot) or ticker_map.get(sym) or 0.0
                        
                        if current_price > 0:
                            db_tick = database.SessionLocal()
                            await self.execute_trade(db_tick, sym, current_price, "COINDCX")
                            db_tick.close()
            except: pass
            await asyncio.sleep(5)

    async def start(self):
        self.is_running = True
        print("✅ DUAL-CORE STATE ENGINE STARTED")
        await asyncio.gather(self.run_delta_loop(), self.run_coindcx_loop())

engine = RealTimeEngine()
