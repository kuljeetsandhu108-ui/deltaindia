import os, re

print("🚀 Initiating the MASSIVE WIN Patcher...")

# --- 1. BACKEND: BACKTESTER.PY UPGRADE ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# Inject Math Shield
b = b.replace('return df.fillna(0)', "df = df.replace([float('inf'), float('-inf')], float('nan'))\n            return df.ffill().bfill().fillna(0)")

# Inject TSL Extraction
b = b.replace("sl_pct, tp_pct = float(logic.get('sl', 0)), float(logic.get('tp', 0))", "sl_pct, tp_pct, tsl_pct = float(logic.get('sl', 0)), float(logic.get('tp', 0)), float(logic.get('tsl', 0))")

# Inject High/Low Tracking
b = b.replace("position = {'entry_price': float(row['close']), 'qty': qty, 'entry_time': row['timestamp']}", "position = {'entry_price': float(row['close']), 'qty': qty, 'entry_time': row['timestamp'], 'highest_seen': float(row['close']), 'lowest_seen': float(row['close'])}")

# Replace exit logic with TSL logic
target_exit = r"if side == 'BUY':\s*if sl_pct > 0 and float\(row\['low'\]\) <= entry \* \(1 - sl_pct/100\): exit_price, reason = entry \* \(1 - sl_pct/100\), 'SL'\s*elif tp_pct > 0 and float\(row\['high'\]\) >= entry \* \(1 \+ tp_pct/100\): exit_price, reason = entry \* \(1 \+ tp_pct/100\), 'TP'\s*else:\s*if sl_pct > 0 and float\(row\['high'\]\) >= entry \* \(1 \+ sl_pct/100\): exit_price, reason = entry \* \(1 \+ sl_pct/100\), 'SL'\s*elif tp_pct > 0 and float\(row\['low'\]\) <= entry \* \(1 - tp_pct/100\): exit_price, reason = entry \* \(1 - tp_pct/100\), 'TP'"

repl_exit = """position['highest_seen'] = max(position['highest_seen'], float(row['high']))
                    position['lowest_seen'] = min(position['lowest_seen'], float(row['low']))
                    
                    if side == 'BUY':
                        if sl_pct > 0 and float(row['low']) <= entry * (1 - sl_pct/100): exit_price, reason = entry * (1 - sl_pct/100), 'SL'
                        elif tp_pct > 0 and float(row['high']) >= entry * (1 + tp_pct/100): exit_price, reason = entry * (1 + tp_pct/100), 'TP'
                        elif tsl_pct > 0 and float(row['low']) <= position['highest_seen'] * (1 - tsl_pct/100): exit_price, reason = position['highest_seen'] * (1 - tsl_pct/100), 'Trailing Stop'
                    else:
                        if sl_pct > 0 and float(row['high']) >= entry * (1 + sl_pct/100): exit_price, reason = entry * (1 + sl_pct/100), 'SL'
                        elif tp_pct > 0 and float(row['low']) <= entry * (1 - tp_pct/100): exit_price, reason = entry * (1 - tp_pct/100), 'TP'
                        elif tsl_pct > 0 and float(row['high']) >= position['lowest_seen'] * (1 + tsl_pct/100): exit_price, reason = position['lowest_seen'] * (1 + tsl_pct/100), 'Trailing Stop'"""
b = re.sub(target_exit, repl_exit, b)

# Inject new Calculate Audit Stats
target_audit = r"def calculate_audit_stats\(self, trades, equity_curve\):[\s\S]*?(?=def run_simulation)"

new_audit = """def calculate_audit_stats(self, trades, equity_curve):
        import numpy as np
        import pandas as pd
        if not trades: return {"profit_factor": 0, "avg_win": 0, "avg_loss": 0, "max_drawdown": 0, "sharpe_ratio": 0, "sortino_ratio": 0, "expectancy": 0, "max_cons_losses": 0, "avg_duration": "0h 0m"}
        wins =[t['pnl'] for t in trades if t['pnl'] > 0]
        losses =[t['pnl'] for t in trades if t['pnl'] <= 0]
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        profit_factor = (sum(wins) / abs(sum(losses))) if sum(losses) != 0 else 999.0
        
        balances = pd.Series([e['balance'] for e in equity_curve])
        drawdowns = (balances - balances.cummax()) / balances.cummax() * 100
        
        returns = balances.pct_change().dropna()
        downside = returns[returns < 0]
        sortino = 0.0
        if not downside.empty and downside.std() != 0:
            sortino = (returns.mean() / downside.std()) * np.sqrt(365 * 24)
            
        max_cons, curr_cons = 0, 0
        for t in trades:
            if t['pnl'] < 0:
                curr_cons += 1
                max_cons = max(max_cons, curr_cons)
            else:
                curr_cons = 0
                
        durations = [(pd.to_datetime(t['exit_time']) - pd.to_datetime(t['entry_time'])).total_seconds() for t in trades]
        avg_sec = np.mean(durations) if durations else 0
        h, rem = divmod(avg_sec, 3600)
        m, _ = divmod(rem, 60)
        
        return {
            "profit_factor": round(float(profit_factor), 2),
            "avg_win": round(float(avg_win), 2),
            "avg_loss": round(float(avg_loss), 2),
            "max_drawdown": round(abs(float(drawdowns.min() if not drawdowns.empty else 0)), 2),
            "sharpe_ratio": round(float(returns.mean() / returns.std() * np.sqrt(365*24)) if returns.std() != 0 else 0, 2),
            "sortino_ratio": round(float(sortino), 2),
            "expectancy": round(float((len(wins)/len(trades) * avg_win) + ((1 - len(wins)/len(trades)) * avg_loss)), 2),
            "max_cons_losses": max_cons,
            "avg_duration": f"{int(h)}h {int(m)}m"
        }

    """
b = re.sub(target_audit, new_audit, b)

with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')


# --- 2. FRONTEND: PAGE.TSX UPGRADE ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# State injections
if 'const[tsl' not in p:
    p = p.replace('const [takeProfit, setTakeProfit] = useState(2.0);', 'const [takeProfit, setTakeProfit] = useState(2.0);\n  const[tsl, setTsl] = useState(0.0);')
    p = p.replace('setTakeProfit(logic.tp || 0);', 'setTakeProfit(logic.tp || 0);\n                    setTsl(logic.tsl || 0);')
    p = p.replace('tp: Number(takeProfit)', 'tp: Number(takeProfit), tsl: Number(tsl)')
    p = p.replace('if (data.tp !== undefined) setTakeProfit(data.tp);', 'if (data.tp !== undefined) setTakeProfit(data.tp);\n            if (data.tsl !== undefined) setTsl(data.tsl);')

    # Risk UI Update
    p = p.replace('<div className="grid grid-cols-2 gap-4">\n                    <div>\n                      <label className="block text-sm text-red-400 mb-1">SL %</label>', 
                  '<div className="grid grid-cols-3 gap-4">\n                    <div>\n                      <label className="block text-sm text-red-400 mb-1">SL %</label>')
    
    target_tp = """                    <div>
                      <label className="block text-sm text-emerald-400 mb-1">TP %</label>
                      <input type="number" step="0.1" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none" />
                    </div>"""
    repl_tsl = target_tp + """
                    <div>
                      <label className="block text-sm text-purple-400 mb-1">Trailing %</label>
                      <input type="number" step="0.1" value={tsl} onChange={(e) => setTsl(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none" />
                    </div>"""
    p = p.replace(target_tp, repl_tsl)

    # Analytics UI Update
    p = p.replace('{backtestResult.metrics.audit.sharpe_ratio}</div></div>', '{backtestResult.metrics.audit.sharpe_ratio} <span className="text-indigo-400 text-sm">/ {backtestResult.metrics.audit.sortino_ratio || "0"} (Sort)</span></div></div>')
    
    append_row = """</div>
                        <div className="grid grid-cols-2 gap-4 mt-4">
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center"><div className="text-slate-500 text-xs uppercase">Max Consecutive Losses</div><div className="text-lg font-bold text-orange-400">{backtestResult.metrics.audit.max_cons_losses} Trades</div></div>
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center"><div className="text-slate-500 text-xs uppercase">Avg Trade Duration</div><div className="text-lg font-bold text-blue-400">{backtestResult.metrics.audit.avg_duration}</div></div>
                        </div>"""
    p = re.sub(r'(<div className="text-lg font-bold text-white">\$\{backtestResult\.metrics\.audit\.expectancy\}</div></div>\s*</div>)', r'\1\n' + append_row, p)

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')


# --- 3. AI ROUTE UPGRADE ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: a = f.read()

if 'tsl:' not in a:
    a = a.replace('- "tp": Take profit percentage (number).', '- "tp": Take profit percentage (number).\n    - "tsl": Trailing stop loss percentage (number, default 0).')
    a = a.replace('"tp": 2.0,', '"tp": 2.0,\n      "tsl": 0.5,')
    with open('./route.ts', 'w') as f: f.write(a)
    os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')

print("✅ MASSIVE WIN SUCCESSFULLY INJECTED!")
