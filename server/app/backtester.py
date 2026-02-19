import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.trend import EMAIndicator, SMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange

class Backtester:
    def __init__(self):
        self.exchange = ccxt.delta({'options': {'defaultType': 'future'}})

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        # Fetch OHLCV data
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

    def calculate_indicators(self, df, logic):
        # Pre-calculate common indicators to ensure speed
        # In a full production app, we would parse 'logic' to only calc what is needed.
        # For MVP, we calculate the basics dynamically based on config.
        
        conditions = logic.get('conditions', [])
        for cond in conditions:
            for side in ['left', 'right']:
                item = cond.get(side)
                if not item or item.get('type') == 'number': continue
                
                name = item.get('type')
                params = item.get('params', {})
                length = int(params.get('length', 14))
                
                if name == 'rsi':
                    df[f'rsi_{length}'] = RSIIndicator(df['close'], window=length).rsi()
                elif name == 'ema':
                    df[f'ema_{length}'] = EMAIndicator(df['close'], window=length).ema_indicator()
                elif name == 'sma':
                    df[f'sma_{length}'] = SMAIndicator(df['close'], window=length).sma_indicator()
                elif name == 'bb_upper':
                    bb = BollingerBands(df['close'], window=length, window_dev=float(params.get('std', 2.0)))
                    df[f'bb_upper_{length}'] = bb.bollinger_hband()
                elif name == 'bb_lower':
                    bb = BollingerBands(df['close'], window=length, window_dev=float(params.get('std', 2.0)))
                    df[f'bb_lower_{length}'] = bb.bollinger_lband()
                    
        return df

    def get_val(self, row, item):
        if item['type'] == 'number': return float(item['params']['value'])
        if item['type'] in ['close', 'open', 'high', 'low', 'volume']: return row[item['type']]
        
        # Indicators
        p = item.get('params', {})
        length = int(p.get('length', 14))
        col = f"{item['type']}_{length}"
        return row.get(col, 0)

    def run_simulation(self, df, logic):
        balance = 1000.0 # Virtual Start Capital
        equity_curve = []
        trades = []
        position = None # None or {'entry_price': X, 'qty': Y, 'sl': Z, 'tp': W}
        
        conditions = logic.get('conditions', [])
        qty = float(logic.get('quantity', 1))
        sl_pct = float(logic.get('sl', 0))
        tp_pct = float(logic.get('tp', 0))

        for i, row in df.iterrows():
            current_price = row['close']
            
            # 1. MANAGE OPEN POSITION
            if position:
                # Check SL (Hit Low)
                if sl_pct > 0 and row['low'] <= position['sl']:
                    exit_price = position['sl']
                    pnl = (exit_price - position['entry_price']) * position['qty']
                    balance += pnl
                    trades.append({'time': row['timestamp'], 'type': 'SELL (SL)', 'price': exit_price, 'pnl': pnl})
                    position = None
                
                # Check TP (Hit High)
                elif tp_pct > 0 and row['high'] >= position['tp']:
                    exit_price = position['tp']
                    pnl = (exit_price - position['entry_price']) * position['qty']
                    balance += pnl
                    trades.append({'time': row['timestamp'], 'type': 'SELL (TP)', 'price': exit_price, 'pnl': pnl})
                    position = None
            
            # 2. CHECK ENTRY CONDITIONS (If no position)
            if not position:
                entry_signal = True
                for cond in conditions:
                    val_left = self.get_val(row, cond['left'])
                    val_right = self.get_val(row, cond['right'])
                    op = cond['operator']
                    
                    if op == 'GREATER_THAN' and not (val_left > val_right): entry_signal = False
                    if op == 'LESS_THAN' and not (val_left < val_right): entry_signal = False
                    if op == 'CROSSES_ABOVE':
                        # Needs previous row logic, simplifying to GT for MVP speed
                        if not (val_left > val_right): entry_signal = False 

                if entry_signal:
                    # Enter Trade
                    sl_price = current_price * (1 - sl_pct/100)
                    tp_price = current_price * (1 + tp_pct/100)
                    position = {'entry_price': current_price, 'qty': qty, 'sl': sl_price, 'tp': tp_price}
                    trades.append({'time': row['timestamp'], 'type': 'BUY', 'price': current_price, 'pnl': 0})

            equity_curve.append({'time': row['timestamp'].isoformat(), 'balance': balance})

        # Final Metrics
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
            "trades": trades[-50:], # Send last 50 trades
            "equity": equity_curve[::5] # Downsample for chart speed
        }

backtester = Backtester()
