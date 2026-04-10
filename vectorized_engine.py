import os, re

print("🧠 Upgrading Core to Vectorized NumPy Math...")

# --- 1. CLEAN MAIN.PY (REMOVE DATE FILTERING HERE) ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: m = f.read()

# Remove the broken date filtering from main.py (we move it to backtester for accuracy)
m = re.sub(r'        s_date = strat\.logic\.get\(\'startDate\'\)[\s\S]*?pd\.Timedelta\(days=1\)\)\]', '', m)
with open('./main.py', 'w') as f: f.write(m)
os.system('docker cp ./main.py app-backend-1:/app/main.py')


# --- 2. UPGRADE BACKTESTER.PY (VECTORIZATION & DATES) ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

vectorized_sim = """    def run_simulation(self, df, logic):
        try:
            if df.empty: return {"error": "No Market Data"}
            import pandas as pd
            import numpy as np
            
            # 1. Calculate indicators on FULL data for absolute accuracy
            df = self.prepare_data(df, logic)
            
            # 2. CALENDAR CONTROL (Slice AFTER indicators are built)
            s_date = logic.get('startDate')
            e_date = logic.get('endDate')
            if s_date and e_date:
                mask = (df['timestamp'] >= pd.to_datetime(s_date)) & (df['timestamp'] <= pd.to_datetime(e_date) + pd.Timedelta(days=1))
                df = df[mask].reset_index(drop=True)
            elif len(df) > 200:
                df = df.iloc[200:].reset_index(drop=True) # Warmup slice
                
            if df.empty: return {"error": "No data available in selected date range."}
            
            # 3. VECTORIZED SIGNAL GENERATION (0.01 second execution)
            entry_signals = pd.Series(True, index=df.index)
            conditions = logic.get('conditions',[])
            
            def get_series(item):
                if item['type'] == 'number': return pd.Series(float(item['params']['value']), index=df.index)
                if item['type'] in['close', 'open', 'high', 'low', 'volume']: return df[item['type']]
                col = f"{item['type']}_{int(item['params'].get('length', 14))}"
                return df.get(col, pd.Series(0, index=df.index))
                
            for cond in conditions:
                l_s = get_series(cond['left'])
                r_s = get_series(cond['right'])
                p_l_s = l_s.shift(1).fillna(0)
                p_r_s = r_s.shift(1).fillna(0)
                op = cond['operator']
                
                if op == 'GREATER_THAN': entry_signals = entry_signals & (l_s > r_s)
                elif op == 'LESS_THAN': entry_signals = entry_signals & (l_s < r_s)
                elif op == 'CROSSES_ABOVE': entry_signals = entry_signals & (l_s > r_s) & (p_l_s <= p_r_s)
                elif op == 'CROSSES_BELOW': entry_signals = entry_signals & (l_s < r_s) & (p_l_s >= p_r_s)
                elif op == 'EQUALS': entry_signals = entry_signals & (l_s == r_s)
                
            # 4. LIGHTWEIGHT EXECUTION LOOP
            balance = 1000.0
            equity_curve, closed_trades = [],[]
            position = None
            
            wallet_pct = float(logic.get('walletPct', 10))
            leverage = float(logic.get('leverage', 1))
            sl_pct, tp_pct, tsl_pct = float(logic.get('sl', 0)), float(logic.get('tp', 0)), float(logic.get('tsl', 0))
            side = logic.get('side', 'BUY').upper()
            FEE = 0.0005
            
            c_arr = df['close'].values
            h_arr = df['high'].values
            l_arr = df['low'].values
            t_arr = df['timestamp'].astype(str).values
            sig_arr = entry_signals.values
            
            for i in range(1, len(df)):
                c, h, l, t, sig = float(c_arr[i]), float(h_arr[i]), float(l_arr[i]), str(t_arr[i]), sig_arr[i]
                
                if position:
                    exit_p, reason = 0.0, ''
                    ent = position['entry_price']
                    position['highest_seen'] = max(position['highest_seen'], h)
                    position['lowest_seen'] = min(position['lowest_seen'], l)
                    
                    if side == 'BUY':
                        if sl_pct > 0 and l <= ent * (1 - sl_pct/100): exit_p, reason = ent * (1 - sl_pct/100), 'SL'
                        elif tp_pct > 0 and h >= ent * (1 + tp_pct/100): exit_p, reason = ent * (1 + tp_pct/100), 'TP'
                        elif tsl_pct > 0 and l <= position['highest_seen'] * (1 - tsl_pct/100): exit_p, reason = position['highest_seen'] * (1 - tsl_pct/100), 'Trailing Stop'
                    else:
                        if sl_pct > 0 and h >= ent * (1 + sl_pct/100): exit_p, reason = ent * (1 + sl_pct/100), 'SL'
                        elif tp_pct > 0 and l <= ent * (1 - tp_pct/100): exit_p, reason = ent * (1 - tp_pct/100), 'TP'
                        elif tsl_pct > 0 and h >= position['lowest_seen'] * (1 + tsl_pct/100): exit_p, reason = position['lowest_seen'] * (1 + tsl_pct/100), 'Trailing Stop'
                        
                    if exit_p > 0:
                        pnl = (exit_p - ent) * position['qty'] if side == 'BUY' else (ent - exit_p) * position['qty']
                        net = pnl - (exit_p * position['qty'] * FEE)
                        balance += net
                        closed_trades.append({'entry_time': position['entry_time'], 'exit_time': t, 'entry_price': round(ent, 5), 'exit_price': round(exit_p, 5), 'qty': round(position['qty'], 5), 'pnl': round(net, 5), 'reason': reason})
                        position = None
                        
                if not position and sig:
                    trade_val = balance * (wallet_pct / 100.0) * leverage
                    q = trade_val / c
                    balance -= (trade_val * FEE)
                    position = {'entry_price': c, 'qty': q, 'entry_time': t, 'highest_seen': c, 'lowest_seen': c}
                    
                if i % 60 == 0:
                    equity_curve.append({'time': t, 'balance': round(balance, 2)})
                    
            wins = [tr for tr in closed_trades if tr['pnl'] > 0]
            total = len(closed_trades)
            win_rate = (len(wins) / total * 100) if total > 0 else 0
            
            # UNLIMITED TRADES RETURNED (Reversed so newest is at the top)
            return {
                "metrics": {
                    "final_balance": round(balance, 2), "total_trades": total, "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "start_date": str(df.iloc[0]["timestamp"]),
                    "end_date": str(df.iloc[-1]["timestamp"]),
                    "audit": self.calculate_audit_stats(closed_trades, equity_curve)
                },
                "trades": closed_trades[::-1],
                "equity": equity_curve
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Sim Error: {str(e)}"}
"""

b = re.sub(r'    def run_simulation[\s\S]*?(?=\Z)', vectorized_sim, b)

with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ Vectorized Array Engine successfully deployed!")
