import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl
import asyncio
from datetime import datetime, timedelta

class Backtester:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def fetch_deep_history(self, symbol, timeframe):
        exchange = None
        try:
            exchange = ccxt.delta({
                'options': {'defaultType': 'future'},
                'timeout': 30000,
                'enableRateLimit': True,
                # Fake Browser User Agent to prevent blocking
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            # Map Timeframe
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')

            # Calculate Start Time (Lookback)
            # 1m -> Last 7 days
            # 1h -> Last 90 days
            # 1d -> Last 365 days
            now = datetime.utcnow()
            if tf == '1m': since = now - timedelta(days=7)
            elif tf == '5m': since = now - timedelta(days=14)
            elif tf == '15m': since = now - timedelta(days=30)
            elif tf == '1h': since = now - timedelta(days=90)
            else: since = now - timedelta(days=365)
            
            since_ts = int(since.timestamp() * 1000)
            
            all_ohlcv = []
            target_candles = 5000 # Fetch up to 5000 candles
            
            print(f"📉 Starting Deep Fetch for {symbol} ({tf})...")

            while len(all_ohlcv) < target_limit:
                # Fetch chunk
                ohlcv = await exchange.fetch_ohlcv(symbol, tf, limit=1000, since=since_ts)
                
                if not ohlcv or len(ohlcv) == 0:
                    break
                
                all_ohlcv.extend(ohlcv)
                
                # Update 'since' to the last timestamp + 1 second
                last_time = ohlcv[-1][0]
                since_ts = last_time + 1
                
                print(f"   ...Fetched {len(ohlcv)} candles (Total: {len(all_ohlcv)})")
                
                # If we got less than requested, we reached the end
                if len(ohlcv) < 1000:
                    break
                    
                # Rate limit sleep
                await asyncio.sleep(0.5)

            if not all_ohlcv: return pd.DataFrame()

            # Create DataFrame
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Remove duplicates just in case
            df = df.drop_duplicates(subset=['timestamp'])
            
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            print(f"✅ Deep Fetch Complete: {len(df)} candles.")
            return df

        except Exception as e:
            print(f"❌ Deep Fetch Error: {str(e)}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def prepare_data(self, df, logic):
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

                    # PURE MATH INDICATORS
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
                        std = float(params.get('std') or 2.0)
                        sma = df['close'].rolling(window=length).mean()
                        rstd = df['close'].rolling(window=length).std()
                        df[col_name] = sma + (rstd * std)
                    elif name == 'bb_lower':
                        std = float(params.get('std') or 2.0)
                        sma = df['close'].rolling(window=length).mean()
                        rstd = df['close'].rolling(window=length).std()
                        df[col_name] = sma - (rstd * std)
            return df.fillna(0)
        except: return df

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

    def calculate_audit_stats(self, trades, equity_curve):
        if not trades: return {"profit_factor": 0, "avg_win": 0, "avg_loss": 0, "max_drawdown": 0, "sharpe_ratio": 0, "expectancy": 0}
        
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] <= 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        profit_factor = (sum(wins) / abs(sum(losses))) if sum(losses) != 0 else 99
        
        bals = [e['balance'] for e in equity_curve]
        peak = bals[0]
        dd = 0
        for b in bals:
            if b > peak: peak = b
            curr = (peak - b) / peak * 100
            if curr > dd: dd = curr
            
        win_rate = len(wins) / len(trades)
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return {
            "profit_factor": round(float(profit_factor), 2),
            "avg_win": round(float(avg_win), 2),
            "avg_loss": round(float(avg_loss), 2),
            "max_drawdown": round(float(dd), 2),
            "sharpe_ratio": 0, # Simplified
            "expectancy": round(float(expectancy), 2)
        }

    def run_simulation(self, df, logic):
        try:
            if df.empty: return {"error": "Failed to load market data"}
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
                        net = pnl - (exit_price * position['qty'] * FEE)
                        balance += net
                        closed_trades.append({
                            'entry_time': position['entry_time'], 'exit_time': row['timestamp'],
                            'entry_price': float(position['entry_price']), 'exit_price': float(exit_price),
                            'type': f"SELL ({reason})", 'pnl': float(net), 'reason': reason
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
                        if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): signal = False
                        if op == 'CROSSES_BELOW' and not (v_l < v_r and p_l >= p_r): signal = False

                    if signal:
                        balance -= (current_price * qty * FEE)
                        position = {'entry_price': current_price, 'qty': qty, 'entry_time': row['timestamp']}

                equity_curve.append({'time': row['timestamp'].isoformat(), 'balance': float(balance), 'buy_hold': float(buy_hold_qty * current_price)})

            wins = len([t for t in closed_trades if t['pnl'] > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            return {
                "metrics": {
                    "final_balance": round(balance, 2),
                    "total_trades": total,
                    "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "audit": self.calculate_audit_stats(closed_trades, equity_curve)
                },
                "trades": closed_trades[-100:],
                "equity": equity_curve[::5]
            }
        except Exception as e:
            print(traceback.format_exc())
            return {"error": f"Sim Error: {str(e)}"}

backtester = Backtester()
target_limit = 5000 # Define global variable for fetch loop
