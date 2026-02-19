import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl

class Backtester:
    def __init__(self):
        # SSL Context Hack for Docker
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        exchange = None
        try:
            if timeframe == '1m': limit = 1000
            
            # Initialize with extended timeout and user agent
            exchange = ccxt.delta({
                'options': {'defaultType': 'future'},
                'timeout': 30000,
                'enableRateLimit': True,
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv: 
                print("⚠️ Warning: Delta returned 0 candles.")
                return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Numeric conversion
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df
        except Exception as e:
            print(f"❌ Data Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def calculate_indicators(self, df, logic):
        # Pure Pandas implementation (No external libs)
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name = item.get('type')
                    params = item.get('params', {})
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
            return df.fillna(0)
        except:
            return df

    def get_val(self, row, item):
        try:
            if item.get('type') == 'number': 
                return float(item.get('params', {}).get('value', 0))
            if item.get('type') in ['close', 'open', 'high', 'low', 'volume']: 
                return row[item.get('type')]
            
            length = int(item.get('params', {}).get('length') or 14)
            col = f"{item.get('type')}_{length}"
            return row.get(col, 0)
        except: return 0

    def run_simulation(self, df, logic):
        try:
            if df.empty: 
                return {"error": "No Market Data. Try different pair/timeframe."}

            df = self.calculate_indicators(df, logic)
            
            balance = 1000.0
            start_price = df.iloc[0]['close']
            buy_hold_qty = 1000.0 / start_price if start_price > 0 else 0
            
            equity_curve = []
            trades = []
            position = None 
            
            conditions = logic.get('conditions', [])
            qty = float(logic.get('quantity', 1))
            sl_pct = float(logic.get('sl', 0))
            tp_pct = float(logic.get('tp', 0))
            FEE = 0.0005 

            for i in range(1, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                current_price = row['close']
                
                # EXIT
                if position:
                    exit_price = 0
                    reason = ''
                    if sl_pct > 0:
                        sl_price = position['entry_price'] * (1 - sl_pct/100)
                        if row['low'] <= sl_price:
                            exit_price = sl_price
                            reason = 'SL'
                    
                    if tp_pct > 0 and exit_price == 0:
                        tp_price = position['entry_price'] * (1 + tp_pct/100)
                        if row['high'] >= tp_price:
                            exit_price = tp_price
                            reason = 'TP'
                    
                    if exit_price > 0:
                        pnl = (exit_price - position['entry_price']) * position['qty']
                        net_pnl = pnl - (exit_price * position['qty'] * FEE)
                        balance += net_pnl
                        trades.append({'time': row['timestamp'], 'type': f'SELL ({reason})', 'price': exit_price, 'pnl': net_pnl})
                        position = None

                # ENTRY
                if not position:
                    entry_signal = True
                    for cond in conditions:
                        val_left = self.get_val(row, cond['left'])
                        val_right = self.get_val(row, cond['right'])
                        prev_left = self.get_val(prev_row, cond['left'])
                        prev_right = self.get_val(prev_row, cond['right'])
                        op = cond['operator']
                        
                        if op == 'GREATER_THAN' and not (val_left > val_right): entry_signal = False
                        if op == 'LESS_THAN' and not (val_left < val_right): entry_signal = False
                        if op == 'CROSSES_ABOVE' and not (val_left > val_right and prev_left <= prev_right): entry_signal = False
                        if op == 'CROSSES_BELOW' and not (val_left < val_right and prev_left >= prev_right): entry_signal = False

                    if entry_signal:
                        balance -= (current_price * qty * FEE)
                        position = {'entry_price': current_price, 'qty': qty}
                        trades.append({'time': row['timestamp'], 'type': 'BUY', 'price': current_price, 'pnl': 0})

                equity_curve.append({
                    'time': row['timestamp'].isoformat(), 
                    'balance': balance, 
                    'buy_hold': buy_hold_qty * current_price
                })

            total_trades = len([t for t in trades if 'SELL' in t['type']])
            wins = len([t for t in trades if t['pnl'] > 0])
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            return {
                "metrics": {
                    "final_balance": round(balance, 2),
                    "total_trades": total_trades,
                    "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2)
                },
                "trades": trades[-50:],
                "equity": equity_curve[::5]
            }
        except Exception as e:
            print(traceback.format_exc())
            return {"error": f"Internal Error: {str(e)}"}

backtester = Backtester()
