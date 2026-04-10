import os, re

print("🚀 Removing 1-Minute Timeframe & Uncapping Trade Limits...")

# --- 1. FRONTEND: Remove 1 Min option ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f:
    c = f.read()

# Surgically remove the 1m option from the HTML
c = c.replace('<option value="1m">1 Min</option>', '')

with open('./page.tsx', 'w') as f:
    f.write(c)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')


# --- 2. BACKEND: Remove Trade Limit ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# Revert the 500 limit back to outputting ALL trades
b = b.replace('"trades": closed_trades[-500:] if len(closed_trades) > 500 else closed_trades,', '"trades": closed_trades,')

with open('./backtester.py', 'w') as f:
    f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')

print("✅ Modifications applied successfully with extreme precision!")
