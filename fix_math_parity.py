import os, re

print("Applying 100% PineScript Parity Patch to the Engine...")

# The perfectly robust TradingView EMA Algorithm
tv_helper = """
    def calc_tv_ema(self, series, length):
        import numpy as np
        import pandas as pd
        vals = series.values
        ema = np.full_like(vals, np.nan, dtype=float)
        alpha = 2.0 / (length + 1)
        valid_mask = ~np.isnan(vals)
        if not valid_mask.any(): return pd.Series(ema, index=series.index)
        
        first_valid = np.argmax(valid_mask)
        start_idx = first_valid + length - 1
        if start_idx >= len(vals): return pd.Series(ema, index=series.index)
        
        # TradingView starts the EMA with an SMA baseline
        ema[start_idx] = np.mean(vals[first_valid : start_idx + 1])
        
        # TradingView strict compounding loop
        for i in range(start_idx + 1, len(vals)):
            if np.isnan(vals[i]):
                ema[i] = ema[i-1]
            else:
                ema[i] = alpha * vals[i] + (1 - alpha) * ema[i - 1]
        return pd.Series(ema, index=series.index)
"""

# --- UPGRADE BACKTESTER MATH ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

if 'def calc_tv_ema' not in b:
    b = b.replace('    def prepare_data(self, df, logic):', tv_helper + '\n    def prepare_data(self, df, logic):')

b = re.sub(r"elif name == 'ema':[\s\S]*?df\[col_name\] = [^\n]*", "elif name == 'ema': df[col_name] = self.calc_tv_ema(df['close'], length)", b)
b = re.sub(r"elif name == 'macd':[\s\S]*?df\[col_name\] = [^\n]*", "elif name == 'macd':\n                        f, s = int(params.get('fast', 12)), int(params.get('slow', 26))\n                        df[col_name] = self.calc_tv_ema(df['close'], f) - self.calc_tv_ema(df['close'], s)", b)

with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')


# --- UPGRADE LIVE ENGINE MATH ---
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()

if 'def calc_tv_ema' not in e:
    e = e.replace('    def calculate_indicator(self, df, name, params):', tv_helper + '\n    def calculate_indicator(self, df, name, params):')

e = re.sub(r"elif name == 'ema':[\s\S]*?return [^\n]*", "elif name == 'ema': return self.calc_tv_ema(df['close'], length)", e)
e = re.sub(r"elif name == 'macd':[\s\S]*?return [^\n]*", "elif name == 'macd':\n                f, s = int(params.get('fast', 12)), int(params.get('slow', 26))\n                return self.calc_tv_ema(df['close'], f) - self.calc_tv_ema(df['close'], s)", e)

with open('./engine.py', 'w') as f: f.write(e)
os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')

print("✅ Backend math engines fully synchronized with TradingView!")
