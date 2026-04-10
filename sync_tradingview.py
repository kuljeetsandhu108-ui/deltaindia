import os, re
print("🔄 Syncing Engine Math with TradingView...")

# --- 1. Upgrade Backtester EMA Math ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

tv_ema_b = """elif name == 'ema':
                        sma = df['close'].rolling(window=length, min_periods=length).mean()
                        ema_base = df['close'].copy()
                        ema_base.iloc[:length] = sma.iloc[:length]
                        df[col_name] = ema_base.ewm(span=length, adjust=False).mean()"""
b = re.sub(r"elif name == 'ema': df\[col_name\] = df\['close'\]\.ewm\(span=length, adjust=False\)\.mean\(\)", tv_ema_b, b)

with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')


# --- 2. Upgrade Live Engine EMA Math ---
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()

tv_ema_e = """elif name == 'ema':
                sma = df['close'].rolling(window=length, min_periods=length).mean()
                ema_base = df['close'].copy()
                ema_base.iloc[:length] = sma.iloc[:length]
                return ema_base.ewm(span=length, adjust=False).mean()"""
e = re.sub(r"elif name == 'ema': return df\['close'\]\.ewm\(span=length, adjust=False\)\.mean\(\)", tv_ema_e, e)

with open('./engine.py', 'w') as f: f.write(e)
os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')


# --- 3. Clean up the duplicate UI Dropdown ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()
pattern = r'<div>\s*<label[^>]*>Action Direction</label>\s*<select[^>]*value=\{side\}[^>]*>[\s\S]*?</select>\s*</div>'
matches = re.findall(pattern, p)
if len(matches) > 1:
    p = p.replace(matches[0], '', 1) # Erase the extra one
    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ TradingView Math successfully injected!")
