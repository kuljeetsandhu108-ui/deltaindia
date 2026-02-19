import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback

class Backtester:
    def __init__(self):
        self.exchange = ccxt.delta({'options': {'defaultType': 'future'}})

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        try:
            if timeframe == '1m': limit = 1000
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Ensure numeric types
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df
        except Exception as e:
            print(f"Data Error: {e}")
            return pd.DataFrame()
        finally:
            await self.exchange.close()

    def calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def prepare_data(self, df, logic):
        # PURE PANDAS CALCULATION (No external libs)
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
                        df[col_name] = self.calculate_rsi(df['close'], length)
                    elif name == 'ema':
                        df[col_name] = df['close'].ewm(span=length, adjust=False).mean()
                    elif name == 'sma':
                        df[col_name] = df['close'].rolling(window=length).mean()
                    
                    # Basic Bollinger Bands (Standard 2.0 dev)
                    elif name == 'bb_upper':
                        sma = df['close'].rolling(window=length).mean()
                        std = df['close'].rolling(window=length).std()
                        df[col_name] = sma + (std * 2)
                    elif name == 'bb_lower':
                        sma = df['close'].rolling(window=length).mean()
                        std = df['close'].rolling(window=length).std()
                        df[col_name] = sma - (std * 2)

            return df.fillna(0)
        except Exception as e:
            print(f"Math Error: {e}")
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
            if df.empty: return {"error": "No Data"}
            df = self.prepare_data(df, logic)
            
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
                
                # EXIT LOGIC
                if position:
                    exit_price = 0
                    reason = ''
                    if sl_pct > 0 and row['low'] <= position['sl']:
                        exit_price = position['sl']
                        reason = 'SL'
                    elif tp_pct > 0 and row['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'TP'
                    
                    if exit_price > 0:
                        pnl = (exit_price - position['entry_price']) * position['qty']
                        net_pnl = pnl - (exit_price * position['qty'] * FEE)
                        balance += net_pnl
                        trades.append({'time': row['timestamp'], 'type': f'SELL ({reason})', 'price': exit_price, 'pnl': net_pnl})
                        position = None

                # ENTRY LOGIC
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
                        
                        if op == 'CROSSES_ABOVE':
                            if not (val_left > val_right and prev_left <= prev_right): entry_signal = False
                        
                        if op == 'CROSSES_BELOW':
                            if not (val_left < val_right and prev_left >= prev_right): entry_signal = False

                    if entry_signal:
                        balance -= (current_price * qty * FEE)
                        sl = current_price * (1 - sl_pct/100)
                        tp = current_price * (1 + tp_pct/100)
                        position = {'entry_price': current_price, 'qty': qty, 'sl': sl, 'tp': tp}
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
            return {"error": f"Backtest Error: {str(e)}"}

backtester = Backtester()
