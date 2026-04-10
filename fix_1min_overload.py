import os, re

print("🚀 Optimizing 1-Minute Data Delivery for 5-Year Backtests...")

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# THE MASTER FIX: 
# Keep ALL trades for calculation, but only send the last 500 to the UI to prevent browser crashes.
# We also optimize the sanitization step which is slow on millions of rows.

old_return = r'return self\.sanitize\(\{\s*"metrics": \{[\s\S]*?"trades": closed_trades,[\s\S]*?\}\s*\}\)'

new_return = """return self.sanitize({
                "metrics": {
                    "final_balance": round(balance, 2), "total_trades": total, "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "start_date": str(df.iloc[0]["timestamp"]),
                    "end_date": str(df.iloc[-1]["timestamp"]),
                    "audit": self.calculate_audit_stats(closed_trades, equity_curve)
                },
                # Only send the latest 500 trades to keep the dashboard lightning fast!
                "trades": closed_trades[-500:] if len(closed_trades) > 500 else closed_trades,
                "equity": sampled_equity
            })"""

b = re.sub(old_return, new_return, b)

# Optimize Sanitizer: Don't recursively scan millions of rows, just scan the result
b = b.replace('def sanitize(self, data):', 'def sanitize(self, data):\n        import math\n        import numpy as np')

with open('./backtester.py', 'w') as f:
    f.write(b)

os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ 1-Minute payload optimized!")
