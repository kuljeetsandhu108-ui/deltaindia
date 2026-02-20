import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl
import math
import time
import asyncio

class Backtester:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def sanitize(self, data):
        """Recursively replaces NaN and Infinity with 0.0 to prevent server crashes"""
        if isinstance(data, (float, np.float64, np.float32, int)):
            if math.isnan(data) or math.isinf(data): return 0.0
            return float(data)
        if isinstance(data, dict):
            return {k: self.sanitize(v) for k, v in data.items()}
        if isinstance(data, list):
            return
        return data

    async def fetch_historical_data(self, symbol, timeframe='1h', target_candles=3000):
        exchange = None
        try:
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            
            exchange = ccxt.delta({
                'options': {'defaultType': 'future'},
                'timeout': 30000,
                'enableRateLimit': True,
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })

            # Milliseconds per timeframe
            ms_map = {'1m': 60000, '5m': 300000, '15m': 900000, '1h': 3600000, '4h': 14400000, '1d': 86400000}
            tf_ms = ms_map.get(tf, 3600000)
            
            # Start time = Current time - (Number of candles * time per candle)
            now_ms = int(time.time() * 1000)
            since_ts = now_ms - (target_candles * tf_ms)
            
            all_ohlcv =[]
            
            # Pagination Loop: Fetch until we hit the target
            while len(all_ohlcv) < target_candles:
                chunk = await exchange.fetch_ohlcv(symbol, tf, since=since_ts, limit=1000)
                if not chunk or len(chunk) == 0:
                    break
                
                all_ohlcv.extend(chunk)
                since_ts = chunk + 1 # Advance pointer to next candle
                
                if len(chunk) < 1000: # We have reached present time
                    break
                
                await asyncio.sleep(0.1) # Don't spam the broker

            if not all_ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(all_ohlcv, columns=)
            df = pd.to_datetime(df, unit='ms')
            
            # Clean data
            df = df.drop_duplicates(subset=).reset_index(drop=True)
            cols =
            df = df.apply(pd.to_numeric, errors='coerce')
            
            return df.dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def prepare_data(self, df, logic):
        # Pure Math - Immune to external library crashes
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name = item.get('type')
                    params = item.get('params', {})
                    try: length = int(params.get('length') or 14)
                    except: length = 14
                    
                    col_name = f"{name}_{length}"
                    if col_name in df.columns: continue

                    try:
                        if name == 'rsi':
                            delta = df.diff()
                            gain = (delta.where(delta > 0, 0)).rolling(window=length, min_periods=1).mean()
                            loss = (-delta.where(delta < 0, 0)).rolling(window=length, min_periods=1).mean()
                            rs = gain / loss
                            df = 100 - (100 / (1 + rs))
                        elif name == 'ema':
                            df = df.ewm(span=length, adjust=False, min_periods=1).mean()
                        elif name == 'sma':
                            df = df.rolling(window=length, min_periods=1).mean()
                    except Exception as inner_e:
                        print(f"Math Error on {name}: {inner_e}")
                        df = 0.0 # Safe fallback

            return df.fillna(0.0) # Destroy any remaining NaNs
        except: return df

    def get_val(self, row, item):
        try:
            if item.get('type') == 'number': return float(item.get('params', {}).get('value', 0))
            if item.get('type') in: return float(row)
            
            try: length = int(item.get('params', {}).get('length') or 14)
            except: length = 14
            
            col = f"{item.get('type')}_{length}"
            return float(row.get(col, 0))
        except: return 0.0

    def calculate_audit_stats(self, trades, equity_curve):
        if not trades or not equity_curve: 
            return {"profit_factor": 0, "avg_win": 0, "avg_loss": 0, "max_drawdown": 0, "sharpe_ratio": 0, "expectancy": 0}
        
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0]
        
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        
        total_loss = abs(sum(losses))
        profit_factor = (sum(wins) / total_loss) if total_loss > 0 else (999.0 if sum(wins) > 0 else 0.0)

        balances = pd.Series( for e in equity_curve])
        peak = balances.cummax()
        drawdowns = (balances - peak) / peak * 100
        max_dd = drawdowns.min() if not drawdowns.empty else 0.0

        returns = balances.pct_change().dropna()
        sharpe = 0.0
        if returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

        win_rate = len(wins) / len(trades) if trades else 0.0
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        return {
            "profit_factor": profit_factor, "avg_win": avg_win, "avg_loss": avg_loss,
            "max_drawdown": abs(max_dd), "sharpe_ratio": sharpe, "expectancy": expectancy
        }

    def run_simulation(self, df, logic):
        try:
            if df is None or df.empty: return {"error": "Failed to pull deep history. Pair might not exist."}
            
            df = self.prepare_data(df, logic)
            
            balance = 1000.0
            start_price = float(df.iloc)
            buy_hold_qty = 1000.0 / start_price if start_price > 0 else 0
            
            equity_curve = []
            closed_trades =[]
            position = None 
            
            conditions = logic.get('conditions',[])
            qty = float(logic.get('quantity', 1))
            sl_pct = float(logic.get('sl', 0))
            tp_pct = float(logic.get('tp', 0))
            FEE = 0.0005 

            for i in range(1, len(df)):
                row = df.iloc
                prev_row = df.iloc
                current_price = float(row)
                
                # --- EXIT ---
                if position:
                    exit_price = 0.0
                    reason = ''
                    entry_price = float(position)
                    
                    if sl_pct > 0 and float(row) <= (entry_price * (1 - sl_pct/100)):
                        exit_price = entry_price * (1 - sl_pct/100)
                        reason = 'SL'
                    elif tp_pct > 0 and float(row) >= (entry_price * (1 + tp_pct/100)):
                        exit_price = entry_price * (1 + tp_pct/100)
                        reason = 'TP'
                    
                    if exit_price > 0:
                        pnl = (exit_price - entry_price) * position
                        cost = (exit_price * position) * FEE
                        net_pnl = pnl - cost
                        balance += net_pnl
                        
                        closed_trades.append({
                            'entry_time': position, 'exit_time': row,
                            'entry_price': entry_price, 'exit_price': exit_price,
                            'qty': position, 'pnl': net_pnl, 'reason': reason, 'type': f"SELL ({reason})"
                        })
                        position = None

                # --- ENTRY ---
                if not position:
                    signal = True
                    for cond in conditions:
                        v_l, v_r = self.get_val(row, cond), self.get_val(row, cond)
                        p_l, p_r = self.get_val(prev_row, cond), self.get_val(prev_row, cond)
                        op = cond
                        
                        if op == 'GREATER_THAN' and not (v_l > v_r): signal = False
                        if op == 'LESS_THAN' and not (v_l < v_r): signal = False
                        if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): signal = False
                        if op == 'CROSSES_BELOW' and not (v_l < v_r and p_l >= p_r): signal = False

                    if signal:
                        cost = (current_price * qty * FEE)
                        balance -= cost
                        position = {'entry_price': current_price, 'qty': qty, 'entry_time': row}

                # Downsample graph points slightly for UI performance
                if i % 2 == 0:
                    equity_curve.append({
                        'time': row.isoformat(), 
                        'balance': float(balance), 
                        'buy_hold': float(buy_hold_qty * current_price)
                    })

            wins = len( > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            result = {
                "metrics": {
                    "final_balance": balance, "total_trades": total, "win_rate": win_rate,
                    "total_return_pct": ((balance - 1000)/1000)*100,
                    "audit": self.calculate_audit_stats(closed_trades, equity_curve)
                },
                "trades": closed_trades,
                "equity": equity_curve
            }
            return self.sanitize(result) # SANITIZE PREVENTS THE 500 CRASH

        except Exception as e:
            # SEND EXACT TRACEBACK TO FRONTEND IF IT FAILS
            error_trace = traceback.format_exc()
            print(f"🔥 SIMULATION CRASH: \n{error_trace}")
            return {"error": f"CRASH: {str(e)}"}

backtester = Backtester()
