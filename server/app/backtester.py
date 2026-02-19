import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl
# IMPORT THE FULL LIBRARY
from ta.trend import EMAIndicator, SMAIndicator, MACD, ADXIndicator, CCIIndicator, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import MFIIndicator, OnBalanceVolumeIndicator

class Backtester:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        exchange = None
        try:
            if timeframe == '1m': limit = 1000
            
            exchange = ccxt.delta({
                'options': {'defaultType': 'future'},
                'timeout': 30000,
                'enableRateLimit': True,
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')

            ohlcv = await exchange.fetch_ohlcv(symbol, tf, limit=limit)
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            return df
        except Exception as e:
            print(f"Data Error: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def prepare_data(self, df, logic):
        # DYNAMIC CALCULATION ENGINE
        # This matches the Live Engine logic perfectly.
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name = item.get('type')
                    params = item.get('params', {})
                    # Default length to 14 if not provided
                    length = int(params.get('length') or 14)
                    col_name = f"{name}_{length}" # Unique ID for column
                    
                    if col_name in df.columns: continue

                    # --- TREND ---
                    if name == 'rsi':
                        df[col_name] = RSIIndicator(df['close'], window=length).rsi()
                    elif name == 'ema':
                        df[col_name] = EMAIndicator(df['close'], window=length).ema_indicator()
                    elif name == 'sma':
                        df[col_name] = SMAIndicator(df['close'], window=length).sma_indicator()
                    elif name == 'macd':
                        # MACD typically 12, 26
                        macd = MACD(df['close'], window_slow=26, window_fast=12)
                        df[col_name] = macd.macd()
                    elif name == 'adx':
                        adx = ADXIndicator(df['high'], df['low'], df['close'], window=length)
                        df[col_name] = adx.adx()
                    elif name == 'cci':
                        cci = CCIIndicator(df['high'], df['low'], df['close'], window=length)
                        df[col_name] = cci.cci()
                    
                    # --- VOLATILITY ---
                    elif name == 'bb_upper':
                        bb = BollingerBands(df['close'], window=length, window_dev=float(params.get('std', 2.0)))
                        df[col_name] = bb.bollinger_hband()
                    elif name == 'bb_lower':
                        bb = BollingerBands(df['close'], window=length, window_dev=float(params.get('std', 2.0)))
                        df[col_name] = bb.bollinger_lband()
                    elif name == 'atr':
                        atr = AverageTrueRange(df['high'], df['low'], df['close'], window=length)
                        df[col_name] = atr.average_true_range()

                    # --- MOMENTUM ---
                    elif name == 'stoch_k':
                        stoch = StochasticOscillator(df['high'], df['low'], df['close'], window=length, smooth_window=3)
                        df[col_name] = stoch.stoch()
                    elif name == 'roc':
                        roc = ROCIndicator(df['close'], window=length)
                        df[col_name] = roc.roc()

                    # --- VOLUME ---
                    elif name == 'mfi':
                        mfi = MFIIndicator(df['high'], df['low'], df['close'], df['volume'], window=length)
                        df[col_name] = mfi.money_flow_index()
                    
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
                current_price = row['close']
                
                # --- EXIT ---
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
                        cost = (exit_price * position['qty']) * FEE
                        net = pnl - cost
                        balance += net
                        closed_trades.append({
                            'entry_time': position['entry_time'], 'exit_time': row['timestamp'],
                            'entry_price': position['entry_price'], 'exit_price': exit_price,
                            'type': f"SELL ({reason})", 'pnl': net, 'reason': reason
                        })
                        position = None

                # --- ENTRY ---
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
                        # True Crossover Logic
                        if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): signal = False
                        if op == 'CROSSES_BELOW' and not (v_l < v_r and p_l >= p_r): signal = False

                    if signal:
                        balance -= (current_price * qty * FEE)
                        position = {'entry_price': current_price, 'qty': qty, 'entry_time': row['timestamp']}

                equity_curve.append({
                    'time': row['timestamp'].isoformat(), 
                    'balance': balance, 
                    'buy_hold': buy_hold_qty * current_price
                })

            wins = len([t for t in closed_trades if t['pnl'] > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # Audit Calcs
            wins_pnl = [t['pnl'] for t in closed_trades if t['pnl'] > 0]
            loss_pnl = [t['pnl'] for t in closed_trades if t['pnl'] <= 0]
            avg_win = np.mean(wins_pnl) if wins_pnl else 0
            avg_loss = np.mean(loss_pnl) if loss_pnl else 0
            
            # Max Drawdown
            bals = [e['balance'] for e in equity_curve]
            peak = bals[0]
            dd = 0
            for b in bals:
                if b > peak: peak = b
                curr_dd = (peak - b) / peak * 100
                if curr_dd > dd: dd = curr_dd

            return {
                "metrics": {
                    "final_balance": round(balance, 2),
                    "total_trades": total,
                    "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "audit": {
                        "max_drawdown": round(dd, 2),
                        "profit_factor": round(sum(wins_pnl)/abs(sum(loss_pnl)), 2) if sum(loss_pnl) != 0 else 99,
                        "avg_win": round(avg_win, 2),
                        "avg_loss": round(avg_loss, 2)
                    }
                },
                "trades": closed_trades[-50:],
                "equity": equity_curve[::5]
            }
        except Exception as e:
            print(traceback.format_exc())
            return {"error": f"Sim Error: {str(e)}"}

backtester = Backtester()
