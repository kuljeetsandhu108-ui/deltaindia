import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.utils import dropna

class Backtester:
    def __init__(self):
        self.exchange = ccxt.delta({'options': {'defaultType': 'future'}})

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Data Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            await self.exchange.close()

    def prepare_data(self, df, logic):
        # 1. CLEAN DATA
        df = dropna(df)
        
        # 2. ADD ALL INDICATORS (The 'ta' library magic)
        # This adds 100+ columns like 'trend_ema_14', 'momentum_rsi', etc.
        try:
            df = add_all_ta_features(
                df, open="open", high="high", low="low", close="close", volume="volume", fillna=True
            )
        except Exception as e:
            print(f"Indicator Calc Error: {e}")

        # 3. CUSTOM MAPPING (Frontend Name -> Library Name)
        # We perform manual calculations for dynamic lengths (e.g. EMA 1 vs EMA 3)
        # because add_all_ta_features only adds standard defaults.
        
        conditions = logic.get('conditions', [])
        for cond in conditions:
            for side in ['left', 'right']:
                item = cond.get(side)
                if not item or item.get('type') == 'number': continue
                
                name = item.get('type')
                params = item.get('params', {})
                length = int(params.get('length', 14))
                col_name = f"{name}_{length}" # e.g. ema_3
                
                # Calculate manually to support ANY length
                if name == 'ema':
                    df[col_name] = df['close'].ewm(span=length, adjust=False).mean()
                elif name == 'sma':
                    df[col_name] = df['close'].rolling(window=length).mean()
                elif name == 'rsi':
                    # Manual RSI calculation for custom lengths
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                    rs = gain / loss
                    df[col_name] = 100 - (100 / (1 + rs))
                elif name == 'close': df[col_name] = df['close']
                elif name == 'open': df[col_name] = df['open']
                elif name == 'high': df[col_name] = df['high']
                elif name == 'low': df[col_name] = df['low']
                
                # Add more custom calcs here if needed (BB, MACD, etc)

        return df.fillna(0)

    def get_val(self, row, item):
        if item['type'] == 'number': return float(item.get('params', {}).get('value', 0))
        if item['type'] in ['close', 'open', 'high', 'low', 'volume']: return row[item['type']]
        
        # Look for the custom column we made above
        length = int(item.get('params', {}).get('length', 14))
        col = f"{item['type']}_{length}"
        
        # Fallback to library defaults if custom col missing
        if col not in row:
            # Try to map to 'ta' library default names
            if item['type'] == 'rsi': return row.get('momentum_rsi', 50)
            if item['type'] == 'adx': return row.get('trend_adx', 0)
            if item['type'] == 'cci': return row.get('trend_cci', 0)
            if item['type'] == 'atr': return row.get('volatility_atr', 0)
            
        return row.get(col, 0)

    def run_simulation(self, df, logic):
        # PREPARE DATA FIRST
        df = self.prepare_data(df, logic)
        
        balance = 1000.0
        start_price = df.iloc[0]['close'] if len(df) > 0 else 1
        buy_hold_qty = 1000.0 / start_price
        
        equity_curve = []
        trades = []
        position = None 
        
        conditions = logic.get('conditions', [])
        qty = float(logic.get('quantity', 1))
        sl_pct = float(logic.get('sl', 0))
        tp_pct = float(logic.get('tp', 0))
        FEE_RATE = 0.0005 

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            current_price = row['close']
            
            # --- EXIT LOGIC ---
            if position:
                exit_price = 0
                reason = ''
                
                # Hit SL?
                if sl_pct > 0 and row['low'] <= position['sl']:
                    exit_price = position['sl']
                    # Slippage simulation: If candle opened below SL, we exited at Open
                    if row['open'] < exit_price: exit_price = row['open']
                    reason = 'SL'
                
                # Hit TP?
                elif tp_pct > 0 and row['high'] >= position['tp']:
                    exit_price = position['tp']
                    if row['open'] > exit_price: exit_price = row['open']
                    reason = 'TP'
                
                if exit_price > 0:
                    gross_pnl = (exit_price - position['entry_price']) * position['qty']
                    fee = (exit_price * position['qty']) * FEE_RATE
                    net_pnl = gross_pnl - fee
                    balance += net_pnl
                    trades.append({'time': row['timestamp'], 'type': f'SELL ({reason})', 'price': exit_price, 'pnl': net_pnl})
                    position = None

            # --- ENTRY LOGIC ---
            if not position:
                entry_signal = True
                for cond in conditions:
                    # Current Values
                    val_left = self.get_val(row, cond['left'])
                    val_right = self.get_val(row, cond['right'])
                    
                    # Previous Values (For Crossovers)
                    prev_left = self.get_val(prev_row, cond['left'])
                    prev_right = self.get_val(prev_row, cond['right'])
                    
                    op = cond['operator']
                    
                    if op == 'GREATER_THAN' and not (val_left > val_right): entry_signal = False
                    if op == 'LESS_THAN' and not (val_left < val_right): entry_signal = False
                    if op == 'EQUALS' and not (val_left == val_right): entry_signal = False
                    
                    # TRUE CROSSOVER LOGIC
                    if op == 'CROSSES_ABOVE':
                        # Current: Left > Right  AND  Previous: Left <= Right
                        if not (val_left > val_right and prev_left <= prev_right): entry_signal = False
                    
                    if op == 'CROSSES_BELOW':
                        # Current: Left < Right  AND  Previous: Left >= Right
                        if not (val_left < val_right and prev_left >= prev_right): entry_signal = False

                if entry_signal:
                    fee = (current_price * qty) * FEE_RATE
                    balance -= fee
                    
                    sl_price = current_price * (1 - sl_pct/100)
                    tp_price = current_price * (1 + tp_pct/100)
                    position = {'entry_price': current_price, 'qty': qty, 'sl': sl_price, 'tp': tp_price}
                    trades.append({'time': row['timestamp'], 'type': 'BUY', 'price': current_price, 'pnl': -fee})

            equity_curve.append({
                'time': row['timestamp'].isoformat(), 
                'balance': balance,
                'buy_hold': buy_hold_qty * current_price
            })

        total_trades = len([t for t in trades if 'SELL' in t['type']])
        wins = len([t for t in trades if t['pnl'] > 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_return = ((balance - 1000) / 1000) * 100

        return {
            "metrics": {
                "final_balance": round(balance, 2),
                "total_trades": total_trades,
                "win_rate": round(win_rate, 1),
                "total_return_pct": round(total_return, 2)
            },
            "trades": trades[-50:],
            "equity": equity_curve[::5]
        }

backtester = Backtester()
