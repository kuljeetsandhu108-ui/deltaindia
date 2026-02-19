import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

class Backtester:
    def __init__(self):
        # Use Global Delta for history (Data is the same)
        self.exchange = ccxt.delta({'options': {'defaultType': 'future'}})

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        try:
            # Map timeframe format if needed
            if timeframe == '1m': limit = 1000
            
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Data Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            await self.exchange.close()

    def prepare_data(self, df, logic):
        # MANUAL CALCULATION (Safe Mode)
        # Only calculate what is requested in the logic
        
        conditions = logic.get('conditions', [])
        for cond in conditions:
            for side in ['left', 'right']:
                item = cond.get(side)
                if not item or item.get('type') == 'number': continue
                
                name = item.get('type')
                params = item.get('params', {})
                length = int(params.get('length', 14))
                col_name = f"{name}_{length}" # Unique name e.g. rsi_14
                
                try:
                    if name == 'rsi':
                        df[col_name] = RSIIndicator(df['close'], window=length).rsi()
                    elif name == 'ema':
                        df[col_name] = EMAIndicator(df['close'], window=length).ema_indicator()
                    elif name == 'sma':
                        df[col_name] = SMAIndicator(df['close'], window=length).sma_indicator()
                    elif name == 'bb_upper':
                        bb = BollingerBands(df['close'], window=length, window_dev=float(params.get('std', 2.0)))
                        df[col_name] = bb.bollinger_hband()
                    elif name == 'bb_lower':
                        bb = BollingerBands(df['close'], window=length, window_dev=float(params.get('std', 2.0)))
                        df[col_name] = bb.bollinger_lband()
                    elif name == 'atr':
                        atr = AverageTrueRange(df['high'], df['low'], df['close'], window=length)
                        df[col_name] = atr.average_true_range()
                    
                    # RAW DATA MAPPING
                    elif name in ['close', 'open', 'high', 'low', 'volume']:
                        df[col_name] = df[name]

                except Exception as e:
                    print(f"Calc Error for {name}: {e}")

        return df.fillna(0)

    def get_val(self, row, item):
        if item['type'] == 'number': return float(item.get('params', {}).get('value', 0))
        if item['type'] in ['close', 'open', 'high', 'low', 'volume']: return row[item['type']]
        
        length = int(item.get('params', {}).get('length', 14))
        col = f"{item['type']}_{length}"
        
        return row.get(col, 0)

    def run_simulation(self, df, logic):
        # Safety check for empty data
        if df.empty: return {"error": "No Data"}

        # 1. Prepare Indicators
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
        FEE_RATE = 0.0005 

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            current_price = row['close']
            
            # --- EXIT LOGIC ---
            if position:
                exit_price = 0
                reason = ''
                
                # Check SL
                if sl_pct > 0:
                    sl_price = position['entry_price'] * (1 - sl_pct/100)
                    if row['low'] <= sl_price:
                        exit_price = sl_price
                        reason = 'SL'
                
                # Check TP
                if tp_pct > 0 and exit_price == 0:
                    tp_price = position['entry_price'] * (1 + tp_pct/100)
                    if row['high'] >= tp_price:
                        exit_price = tp_price
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
                    val_left = self.get_val(row, cond['left'])
                    val_right = self.get_val(row, cond['right'])
                    
                    prev_left = self.get_val(prev_row, cond['left'])
                    prev_right = self.get_val(prev_row, cond['right'])
                    
                    op = cond['operator']
                    
                    if op == 'GREATER_THAN' and not (val_left > val_right): entry_signal = False
                    if op == 'LESS_THAN' and not (val_left < val_right): entry_signal = False
                    if op == 'EQUALS' and not (val_left == val_right): entry_signal = False
                    
                    if op == 'CROSSES_ABOVE':
                        # Valid Crossover: Now > Target AND Prev <= Target
                        if not (val_left > val_right and prev_left <= prev_right): entry_signal = False
                    
                    if op == 'CROSSES_BELOW':
                        if not (val_left < val_right and prev_left >= prev_right): entry_signal = False

                if entry_signal:
                    # Calculate cost
                    cost = current_price * qty
                    fee = cost * FEE_RATE
                    
                    # Check if we have enough balance (Virtual)
                    if balance > fee:
                        balance -= fee
                        position = {'entry_price': current_price, 'qty': qty}
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
            "trades": trades[-50:], # Last 50 trades
            "equity": equity_curve[::5] # Downsample for chart performance
        }

backtester = Backtester()
