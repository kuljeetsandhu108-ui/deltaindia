import os, re

print("🔓 Unlocking Full Chronological Ledger (2021-2026)...")

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# THE MASTER FIX: 
# 1. Remove the "Significant Trades" logic that was hiding your 2026 data.
# 2. Return the FULL list of trades.
# 3. Sort them by entry_time descending (Newest First).

old_logic = r'# 🚀 DATA PAYLOAD COMPRESSION[\s\S]*?display_trades = closed_trades\[::-1\]'

new_logic = """# 🚀 FULL CHRONOLOGICAL LEDGER
            # We send every single trade from the chosen date range, Newest First.
            display_trades = sorted(closed_trades, key=lambda x: x['entry_time'], reverse=True)"""

b = re.sub(old_logic, new_logic, b)

with open('./backtester.py', 'w') as f:
    f.write(b)

os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ Trade limits completely removed. 2026 data restored to top of list!")
