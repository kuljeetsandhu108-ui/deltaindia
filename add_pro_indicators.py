import os

print("Injecting Pro Indicators (MACD, VWAP, Bollinger, ATR)...")

# --- 1. Upgrade Engine.py (Live Trading) ---
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()

e_start = "    def calculate_indicator(self, df, name, params):"
e_end = "    async def check_conditions"

new_e = """    def calculate_indicator(self, df, name, params):
        import pandas as pd
        import numpy as np
        try:
            length = int(params.get('length') or 14)
            if name == 'rsi':
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                return 100 - (100 / (1 + (gain / loss)))
            elif name == 'ema': return df['close'].ewm(span=length, adjust=False).mean()
            elif name == 'sma': return df['close'].rolling(window=length).mean()
            elif name == 'macd':
                f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                return df['close'].ewm(span=f, adjust=False).mean() - df['close'].ewm(span=s, adjust=False).mean()
            elif name == 'bb_upper':
                std = float(params.get('std', 2.0))
                return df['close'].rolling(window=length).mean() + (df['close'].rolling(window=length).std() * std)
            elif name == 'bb_lower':
                std = float(params.get('std', 2.0))
                return df['close'].rolling(window=length).mean() - (df['close'].rolling(window=length).std() * std)
            elif name == 'atr':
                tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                return tr.rolling(window=length).mean()
            elif name == 'vwap':
                tp = (df['high'] + df['low'] + df['close']) / 3
                return (tp * df['volume']).rolling(window=length).sum() / df['volume'].rolling(window=length).sum()
            return pd.Series(0, index=df.index)
        except: return pd.Series(0, index=df.index)

"""

if e_start in e and e_end in e:
    e = e[:e.find(e_start)] + new_e + e[e.find(e_end):]
    with open('./engine.py', 'w') as f: f.write(e)
    os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')


# --- 2. Upgrade Backtester.py (Simulations) ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

b_start = "    def prepare_data(self, df, logic):"
b_end = "    def get_val("

new_b = """    def prepare_data(self, df, logic):
        import pandas as pd
        import numpy as np
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    name = item.get('type')
                    params = item.get('params', {})
                    try: length = int(params.get('length') or 14)
                    except: length = 14
                    
                    col_name = f"{name}_{length}"
                    if col_name in df.columns: continue

                    if name == 'rsi':
                        delta = df['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                        df[col_name] = 100 - (100 / (1 + (gain / loss)))
                    elif name == 'ema': df[col_name] = df['close'].ewm(span=length, adjust=False).mean()
                    elif name == 'sma': df[col_name] = df['close'].rolling(window=length).mean()
                    elif name == 'macd':
                        f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                        df[col_name] = df['close'].ewm(span=f, adjust=False).mean() - df['close'].ewm(span=s, adjust=False).mean()
                    elif name == 'bb_upper':
                        std = float(params.get('std', 2.0))
                        df[col_name] = df['close'].rolling(window=length).mean() + (df['close'].rolling(window=length).std() * std)
                    elif name == 'bb_lower':
                        std = float(params.get('std', 2.0))
                        df[col_name] = df['close'].rolling(window=length).mean() - (df['close'].rolling(window=length).std() * std)
                    elif name == 'atr':
                        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                        df[col_name] = tr.rolling(window=length).mean()
                    elif name == 'vwap':
                        tp = (df['high'] + df['low'] + df['close']) / 3
                        df[col_name] = (tp * df['volume']).rolling(window=length).sum() / df['volume'].rolling(window=length).sum()
            return df.fillna(0)
        except: return df

"""

if b_start in b and b_end in b:
    b = b[:b.find(b_start)] + new_b + b[b.find(b_end):]
    with open('./backtester.py', 'w') as f: f.write(b)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')


# --- 3. Add VWAP to Frontend UI Dropdown ---
os.system('docker cp app-frontend-1:/app/lib/indicators.ts ./indicators.ts')
with open('./indicators.ts', 'r') as f: i = f.read()

if "'vwap'" not in i:
    target = "{ value: 'macd', label: 'MACD Line', params: [{name: 'fast', def: 12}, {name: 'slow', def: 26}, {name: 'sig', def: 9}] },"
    replacement = target + "\n  { value: 'vwap', label: 'VWAP (Volume Weighted Avg Price)', params: [{name: 'length', def: 14}] },"
    i = i.replace(target, replacement)
    with open('./indicators.ts', 'w') as f: f.write(i)
    os.system('docker cp ./indicators.ts app-frontend-1:/app/lib/indicators.ts')

print("✅ Indicators added successfully!")
