import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl
import math

class Backtester:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def sanitize(self, data):
        # Prevents crash if math returns NaN/Infinity
        if isinstance(data, float):
            if math.isnan(data) or math.isinf(data): return 0.0
            return data
        if isinstance(data, dict):
            return {k: self.sanitize(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.sanitize(i) for i in data]
        return data

    async def fetch_historical_data(self, symbol, timeframe='1h'):
        exchange = None
        try:
            print("--- 1. FETCHING DATA ---")
            exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'timeout': 30000})
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            limit = 2000 if tf == '1m' else 1000
            ohlcv = await exchange.fetch_ohlcv(symbol, tf, limit=limit)
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            return df.dropna()
        except Exception as e:
            print(f"FETCH ERROR: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def prepare_data(self, df, logic):
        print("--- 2. CALCULATING INDICATORS ---")
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name = item.get('type')
                    params = item.get('params', {})
                    try: length = int(params.get('length') or 14)
                    except: length = 14
                    
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
            
            return df.fillna(0)
        except Exception as e:
            print(f"INDICATOR MATH ERROR: {traceback.format_exc()}")
            return df

    def get_val(self, row, item):
        try:
            if item.get('type') == 'number': return float(item.get('params', {}).get('value', 0))
            if item.get('type') in ['close', 'open', 'high', 'low', 'volume']: return float(row[item.get('type')])
            
            try: length = int(item.get('params', {}).get('length') or 14)
            except: length = 14
            
            col = f"{item.get('type')}_{length}"
            return float(row.get(col, 0))
        except: return 0.0

    def run_simulation(self, df, logic):
        try:
            if df.empty: return {"error": "No Market Data"}
            df = self.prepare_data(df, logic)
            print("--- 3. RUNNING SIMULATION ---")
            
            balance, start_price = 1000.0, float(df.iloc[0]['close'])
            buy_hold_qty = 1000.0 / start_price if start_price > 0 else 0
            
            equity_curve, closed_trades, position = [], [], None
            
            conditions = logic.get('conditions', [])
            qty, sl_pct, tp_pct = float(logic.get('quantity', 1)), float(logic.get('sl', 0)), float(logic.get('tp', 0))
            FEE = 0.0005 

            for i in range(1, len(df)):
                row, prev_row = df.iloc[i], df.iloc[i-1]
                
                # --- EXIT ---
                if position:
                    exit_price, reason = 0.0, ''
                    entry_price = float(position['entry_price'])
                    if sl_pct > 0:
                        sl_price = entry_price * (1 - sl_pct/100)
                        if float(row['low']) <= sl_price: exit_price, reason = sl_price, 'SL'
                    
                    if tp_pct > 0 and exit_price == 0:
                        tp_price = entry_price * (1 + tp_pct/100)
                        if float(row['high']) >= tp_price: exit_price, reason = tp_price, 'TP'
                    
                    if exit_price > 0:
                        pnl = (exit_price - entry_price) * position['qty']
                        net_pnl = pnl - (exit_price * position['qty'] * FEE)
                        balance += net_pnl
                        closed_trades.append({'entry_time': position['entry_time'], 'exit_time': row['timestamp'], 'entry_price': entry_price, 'exit_price': exit_price, 'pnl': net_pnl, 'reason': reason})
                        position = None

                # --- ENTRY ---
                if not position:
                    signal = True
                    for cond in conditions:
                        v_l, v_r = self.get_val(row, cond['left']), self.get_val(row, cond['right'])
                        p_l, p_r = self.get_val(prev_row, cond['left']), self.get_val(prev_row, cond['right'])
                        op = cond['operator']
                        
                        if op == 'GREATER_THAN' and not (v_l > v_r): signal = False
                        if op == 'LESS_THAN' and not (v_l < v_r): signal = False
                        if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): signal = False
                        if op == 'CROSSES_BELOW' and not (val_left < val_right and prev_left >= prev_right): signal = False

                    if signal:
                        cost = (float(row['close']) * qty * FEE)
                        balance -= cost
                        position = {'entry_price': float(row['close']), 'qty': qty, 'entry_time': row['timestamp']}

                equity_curve.append({'time': row['timestamp'].isoformat(), 'balance': float(balance), 'buy_hold': float(buy_hold_qty * float(row['close']))})

            print("--- 4. CALCULATING STATS ---")
            wins = len([t for t in closed_trades if t['pnl'] > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            result = {
                "metrics": {
                    "final_balance": round(balance, 2), "total_trades": total, "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2), "audit": {}
                },
                "trades": closed_trades[-50:],
                "equity": equity_curve[::5]
            }
            return self.sanitize(result)

        except Exception as e:
            print(f"🔥 SIMULATION CRASH: {traceback.format_exc()}")
            return {"error": f"Sim Error: {str(e)}"}

backtester = Backtester()
