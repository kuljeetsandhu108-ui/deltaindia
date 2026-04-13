import os, re

print("==================================================")
print("🩺 RUNNING INDICATOR DIAGNOSTIC & REPAIR...")
print("==================================================")

# --- 1. CHECK AND REPAIR UI DROPDOWN (indicators.ts) ---
os.system('docker cp app-frontend-1:/app/lib/indicators.ts ./indicators.ts')
with open('./indicators.ts', 'r') as f: i = f.read()

new_inds = """  { value: 'hma', label: 'Hull Moving Average (HMA)', params:[{name: 'length', def: 14}] },
  { value: 'williams_r', label: 'Williams %R', params:[{name: 'length', def: 14}] },
  { value: 'mom', label: 'Momentum Oscillator', params: [{name: 'length', def: 10}] },
  { value: 'tsi', label: 'True Strength Index (TSI)', params:[{name: 'long_length', def: 25}, {name: 'short_length', def: 13}] },
  { value: 'uo', label: 'Ultimate Oscillator', params:[{name: 'fast', def: 7}, {name: 'mid', def: 14}, {name: 'slow', def: 28}] },\n"""

if 'williams_r' not in i:
    print("❌ Diagnostic: Indicators missing from UI Dropdown. Repairing...")
    # Use Regex to ignore spaces around the equals sign and bracket
    i = re.sub(r'export const INDICATORS\s*=\s*\[', 'export const INDICATORS =[\n' + new_inds, i, count=1)
    with open('./indicators.ts', 'w') as f: f.write(i)
    os.system('docker cp ./indicators.ts app-frontend-1:/app/lib/indicators.ts')
    print("   ✅ Repair Successful: UI Dropdown updated.")
else:
    print("✅ Diagnostic: UI Dropdown already contains the indicators.")


# --- 2. CHECK AND REPAIR AI PROMPT (route.ts) ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

if 'williams_r' not in r:
    print("❌ Diagnostic: AI prompt missing new indicators. Repairing...")
    # Add simple length indicators
    r = re.sub(r"('adx', 'cci', 'roc')", r"\1, 'hma', 'williams_r', 'mom'", r)
    # Add complex indicators
    new_ai_params = """    - 'tsi' -> params: { "long_length": 25, "short_length": 13 }
    - 'uo' -> params: { "fast": 7, "mid": 14, "slow": 28 }\n"""
    r = r.replace("- 'macd' ->", new_ai_params + "    - 'macd' ->")
    with open('./route.ts', 'w') as f: f.write(r)
    os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')
    print("   ✅ Repair Successful: AI trained on new parameters.")
else:
    print("✅ Diagnostic: AI Prompt already trained.")


# --- 3. CHECK AND REPAIR UI GUARDS (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

if 'williams_r' not in p:
    print("❌ Diagnostic: UI Parameter Guards missing. Repairing...")
    p = re.sub(r"\['ema','sma','rsi','vwap','atr','adx','cci','roc'\]", "['ema','sma','rsi','vwap','atr','adx','cci','roc','hma','williams_r','mom']", p)
    new_ui_guards = """                            if (type === 'tsi') {
                                if (!params.long_length) params.long_length = 25;
                                if (!params.short_length) params.short_length = 13;
                            }
                            if (type === 'uo') {
                                if (!params.fast) params.fast = 7;
                                if (!params.mid) params.mid = 14;
                                if (!params.slow) params.slow = 28;
                            }\n"""
    p = p.replace("if (type === 'macd') {", new_ui_guards + "                            if (type === 'macd') {")
    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
    print("   ✅ Repair Successful: UI Guards fortified.")
else:
    print("✅ Diagnostic: UI Guards already installed.")


# --- 4. CHECK AND REPAIR MATH ENGINES ---
math_logic = """                    elif name == 'williams_r':
                        hh = df['high'].rolling(window=length).max()
                        ll = df['low'].rolling(window=length).min()
                        RES_TARGET = (hh - df['close']) / (hh - ll) * -100
                    elif name == 'mom':
                        RES_TARGET = df['close'] - df['close'].shift(length)
                    elif name == 'hma':
                        half_l, sqrt_l = int(length / 2), int(np.sqrt(length))
                        def wma(s, l):
                            weights = np.arange(1, l + 1)
                            return s.rolling(l).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
                        diff = 2 * wma(df['close'], half_l) - wma(df['close'], length)
                        RES_TARGET = wma(diff, sqrt_l)
                    elif name == 'tsi':
                        long_l, short_l = int(params.get('long_length', 25)), int(params.get('short_length', 13))
                        diff = df['close'].diff()
                        num = self.calc_tv_ema(self.calc_tv_ema(diff, long_l), short_l)
                        den = self.calc_tv_ema(self.calc_tv_ema(diff.abs(), long_l), short_l)
                        RES_TARGET = 100 * (num / den)
                    elif name == 'uo':
                        fast, mid, slow = int(params.get('fast', 7)), int(params.get('mid', 14)), int(params.get('slow', 28))
                        prev_close = df['close'].shift(1)
                        bp = df['close'] - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                        tr = pd.concat([df['high'], prev_close], axis=1).max(axis=1) - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                        a1 = bp.rolling(fast).sum() / tr.rolling(fast).sum()
                        a2 = bp.rolling(mid).sum() / tr.rolling(mid).sum()
                        a3 = bp.rolling(slow).sum() / tr.rolling(slow).sum()
                        RES_TARGET = 100 * (4 * a1 + 2 * a2 + a3) / 7\n"""

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()
if 'williams_r' not in b:
    print("❌ Diagnostic: Math missing in Backtester. Repairing...")
    bt_math = math_logic.replace('RES_TARGET =', 'df[col_name] =')
    b = b.replace("elif name == 'ema':", bt_math + "                    elif name == 'ema':")
    with open('./backtester.py', 'w') as f: f.write(b)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
    print("   ✅ Repair Successful: Backtester Math upgraded.")

os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()
if 'williams_r' not in e:
    print("❌ Diagnostic: Math missing in Engine. Repairing...")
    en_math = math_logic.replace('RES_TARGET =', 'return ')
    e = e.replace("elif name == 'ema':", en_math + "                    elif name == 'ema':")
    with open('./engine.py', 'w') as f: f.write(e)
    os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')
    print("   ✅ Repair Successful: Engine Math upgraded.")

print("==================================================")
print("🏁 FULL DIAGNOSTIC & REPAIR COMPLETE!")
print("==================================================")
