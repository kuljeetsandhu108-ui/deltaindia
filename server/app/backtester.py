import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl

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

            # Map Timeframe
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
        # Calculate Indicators (RSI, EMA, etc)
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
        except: return df

    def get_val(self, row, item):
        try:
            if item.get('type') == 'number': return float(item.get('params', {}).get('value', 0))
            if item.get('type') in ['close', 'open', 'high', 'low', 'volume']: return row[item.get('type')]
            length = int(item.get('params', {}).get('length') or 14)
            col = f"{item.get('type')}_{length}"
            return row.get(col, 0)
        except: return 0

    def calculate_audit_stats(self, trades, equity_curve):
        # 1. win/loss stats
        if not trades: return {}
        
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] <= 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        win_rate = len(wins) / len(trades) * 100
        profit_factor = (sum(wins) / abs(sum(losses))) if sum(losses) != 0 else 999

        # 2. streaks
        streaks = []
        current_streak = 0
        for t in trades:
            if t['pnl'] > 0:
                current_streak = current_streak + 1 if current_streak > 0 else 1
            else:
                current_streak = current_streak - 1 if current_streak < 0 else -1
            streaks.append(current_streak)
        
        max_consecutive_wins = max(streaks) if streaks else 0
        max_consecutive_losses = abs(min(streaks)) if streaks else 0

        # 3. drawdown
        balances = [e['balance'] for e in equity_curve]
        peak = balances[0]
        max_drawdown = 0
        for b in balances:
            if b > peak: peak = b
            dd = (peak - b) / peak * 100
            if dd > max_drawdown: max_drawdown = dd

        # 4. sharpe (Daily Resample)
        df_eq = pd.DataFrame(equity_curve)
        df_eq['time'] = pd.to_datetime(df_eq['time'])
        df_eq.set_index('time', inplace=True)
        # Resample to daily to calculate standard sharpe
        daily_returns = df_eq['balance'].resample('D').last().pct_change().dropna()
        
        sharpe = 0
        if daily_returns.std() != 0:
            # Annualized Sharpe (assuming 365 days for crypto)
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(365)

        return {
            "profit_factor": round(profit_factor, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_win_streak": max_consecutive_wins,
            "max_loss_streak": max_consecutive_losses,
            "expectancy": round((win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss), 2)
        }

    def run_simulation(self, df, logic):
        try:
            if df.empty: return {"error": "No Market Data"}
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
                current_price = row['close']
                prev_row = df.iloc[i-1]
                
                # --- EXIT ---
                if position:
                    exit_price = 0
                    reason = ''
                    if sl_pct > 0 and row['low'] <= position['sl']:
                        exit_price = position['sl']
                        reason = 'Stop Loss'
                    elif tp_pct > 0 and row['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'Take Profit'
                    
                    if exit_price > 0:
                        pnl = (exit_price - position['entry_price']) * position['qty']
                        net = pnl - (exit_price * position['qty'] * FEE)
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
                        if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): signal = False
                        if op == 'CROSSES_BELOW' and not (v_l < v_r and p_l >= p_r): signal = False

                    if signal:
                        balance -= (current_price * qty * FEE)
                        sl = current_price * (1 - sl_pct/100)
                        tp = current_price * (1 + tp_pct/100)
                        position = {'entry_price': current_price, 'qty': qty, 'sl': sl, 'tp': tp, 'entry_time': row['timestamp']}

                equity_curve.append({
                    'time': row['timestamp'].isoformat(), 
                    'balance': balance, 
                    'buy_hold': buy_hold_qty * current_price
                })

            wins = len([t for t in closed_trades if t['pnl'] > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # CALCULATE ADVANCED STATS
            audit = self.calculate_audit_stats(closed_trades, equity_curve)

            return {
                "metrics": {
                    "final_balance": round(balance, 2),
                    "total_trades": total,
                    "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "audit": audit # NEW AUDIT SECTION
                },
                "trades": closed_trades[-50:],
                "equity": equity_curve[::5]
            }
        except Exception as e:
            print(traceback.format_exc())
            return {"error": f"Sim Error: {str(e)}"}

backtester = Backtester()
