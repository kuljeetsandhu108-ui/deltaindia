import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl
import math

# NO EXTERNAL TA LIBRARIES IMPORTED HERE
# PURE PYTHON/PANDAS ONLY

class Backtester:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def sanitize(self, data):
        if isinstance(data, float):
            if math.isnan(data) or math.isinf(data): return 0.0
            return data
        if isinstance(data, dict):
            return {k: self.sanitize(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.sanitize(i) for i in data]
        return data

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        exchange = None
        try:
            # Map timeframe
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            
            # Fetch deeper history for small timeframes
            if tf == '1m': limit = 2000
            
            exchange = ccxt.delta({
                'options': {'defaultType': 'future'},
                'timeout': 30000,
                'enableRateLimit': True,
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            ohlcv = await exchange.fetch_ohlcv(symbol, tf, limit=limit)
            
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df.dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def prepare_data(self, df, logic):
        # MANUAL MATH ENGINE (Zero Dependencies)
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name = item.get('type')
                    params = item.get('params', {})
                    # Ensure length is a valid integer, default to 14
                    try:
                        length = int(params.get('length') or 14)
                    except:
                        length = 14
                        
                    col_name = f"{name}_{length}"
                    
                    if col_name in df.columns: continue

                    # --- PURE PANDAS IMPLEMENTATIONS ---
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
                        
                    elif name == 'bb_upper':
                        std_dev = float(params.get('std') or 2.0)
                        sma = df['close'].rolling(window=length).mean()
                        std = df['close'].rolling(window=length).std()
                        df[col_name] = sma + (std * std_dev)
                        
                    elif name == 'bb_lower':
                        std_dev = float(params.get('std') or 2.0)
                        sma = df['close'].rolling(window=length).mean()
                        std = df['close'].rolling(window=length).std()
                        df[col_name] = sma - (std * std_dev)

            return df.fillna(0)
        except Exception as e:
            print(f"Math Calculation Error: {e}")
            return df

    def get_val(self, row, item):
        try:
            if item.get('type') == 'number': 
                return float(item.get('params', {}).get('value', 0))
            if item.get('type') in ['close', 'open', 'high', 'low', 'volume']: 
                return float(row[item.get('type')])
            
            try: length = int(item.get('params', {}).get('length') or 14)
            except: length = 14
            
            col = f"{item.get('type')}_{length}"
            return float(row.get(col, 0))
        except: return 0.0

    def run_simulation(self, df, logic):
        try:
            if df.empty: return {"error": "No Market Data"}
            df = self.prepare_data(df, logic)
            
            balance = 1000.0
            start_price = float(df.iloc[0]['close'])
            buy_hold_qty = 1000.0 / start_price if start_price > 0 else 0
            
            equity_curve = []
            closed_trades = []
            position = None 
            
            conditions = logic.get('conditions', [])
            qty = float(logic.get('quantity', 1))
            sl_pct = float(logic.get('sl', 0))
            tp_pct = float(logic.get('tp', 0))
            FEE = 0.0005 

            for i in range(1, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                current_price = float(row['close'])
                
                # EXIT
                if position:
                    exit_price = 0.0
                    reason = ''
                    entry_price = float(position['entry_price'])
                    
                    if sl_pct > 0:
                        sl_price = entry_price * (1 - sl_pct/100)
                        if float(row['low']) <= sl_price:
                            exit_price = sl_price
                            reason = 'SL'
                    
                    if tp_pct > 0 and exit_price == 0:
                        tp_price = entry_price * (1 + tp_pct/100)
                        if float(row['high']) >= tp_price:
                            exit_price = tp_price
                            reason = 'TP'
                    
                    if exit_price > 0:
                        pnl = (exit_price - entry_price) * position['qty']
                        cost = (exit_price * position['qty']) * FEE
                        net_pnl = pnl - cost
                        balance += net_pnl
                        
                        closed_trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': row['timestamp'],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'qty': float(position['qty']),
                            'pnl': net_pnl,
                            'reason': reason,
                            'type': f"SELL ({reason})"
                        })
                        position = None

                # ENTRY
                if not position:
                    signal = True
                    for cond in conditions:
                        v_l = self.get_val(row, cond['left'])
                        v_r = self.get_val(row, cond['right'])
                        p_l = self.get_val(prev_row, cond['left'])
                        p_r = self.get_val(prev_row, cond['right'])
                        op = cond['operator']
                        
                        if op == 'GREATER_THAN' and not (v_l > v_r): signal = False
                        if op == 'LESS_THAN' and not (v_l < v_r): signal = False
                        if op == 'CROSSES_ABOVE':
                            if not (v_l > v_r and p_l <= p_r): signal = False
                        if op == 'CROSSES_BELOW':
                            if not (val_left < val_right and prev_left >= prev_right): signal = False

                    if signal:
                        cost = (current_price * qty * FEE)
                        balance -= cost
                        position = {'entry_price': current_price, 'qty': qty, 'entry_time': row['timestamp']}

                equity_curve.append({
                    'time': row['timestamp'].isoformat(), 
                    'balance': float(balance), 
                    'buy_hold': float(buy_hold_qty * current_price)
                })

            wins = len([t for t in closed_trades if t['pnl'] > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            result = {
                "metrics": {
                    "final_balance": round(balance, 2),
                    "total_trades": total,
                    "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "audit": {
                        "max_drawdown": 0, "profit_factor": 0, "expectancy": 0
                    }
                },
                "trades": closed_trades[-50:],
                "equity": equity_curve[::5]
            }
            return self.sanitize(result)

        except Exception as e:
            print(traceback.format_exc())
            return {"error": f"Sim Error: {str(e)}"}

backtester = Backtester()
