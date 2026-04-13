import os, re

print("📈 Injecting HMA, Williams %R, MOM, TSI, and Ultimate Oscillator...")

# --- 1. UPGRADE UI DROPDOWN (indicators.ts) ---
os.system('docker cp app-frontend-1:/app/lib/indicators.ts ./indicators.ts')
with open('./indicators.ts', 'r') as f: i = f.read()

new_inds = """  { value: 'hma', label: 'Hull Moving Average (HMA)', params:[{name: 'length', def: 14}] },
  { value: 'williams_r', label: 'Williams %R', params: [{name: 'length', def: 14}] },
  { value: 'mom', label: 'Momentum Oscillator', params: [{name: 'length', def: 10}] },
  { value: 'tsi', label: 'True Strength Index (TSI)', params:[{name: 'long_length', def: 25}, {name: 'short_length', def: 13}] },
  { value: 'uo', label: 'Ultimate Oscillator', params:[{name: 'fast', def: 7}, {name: 'mid', def: 14}, {name: 'slow', def: 28}] },\n"""

if 'hma' not in i:
    i = i.replace('export const INDICATORS = [', 'export const INDICATORS =[\n' + new_inds)
    with open('./indicators.ts', 'w') as f: f.write(i)
    os.system('docker cp ./indicators.ts app-frontend-1:/app/lib/indicators.ts')


# --- 2. UPGRADE AI PROMPT (route.ts) ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

if 'williams_r' not in r:
    r = re.sub(r"(- 'ema', 'sma', 'wma', 'rsi'.*?-> params: \{ \"length\": number \})", r"\1\n    - 'hma', 'williams_r', 'mom' -> params: { \"length\": number }", r)
    
    new_ai_params = """    - 'tsi' -> params: { "long_length": 25, "short_length": 13 }
    - 'uo' -> params: { "fast": 7, "mid": 14, "slow": 28 }"""
    r = r.replace('- \'psar\'', new_ai_params + '\n    - \'psar\'')
    
    with open('./route.ts', 'w') as f: f.write(r)
    os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')


# --- 3. UPGRADE UI GUARDS (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

if 'williams_r' not in p:
    p = p.replace("'aroon_down']", "'aroon_down','hma','williams_r']")
    
    new_ui_guards = """                            if (type === 'mom' && !params.length) params.length = 10;
                            if (type === 'tsi') {
                                if (!params.long_length) params.long_length = 25;
                                if (!params.short_length) params.short_length = 13;
                            }
                            if (type === 'uo') {
                                if (!params.fast) params.fast = 7;
                                if (!params.mid) params.mid = 14;
                                if (!params.slow) params.slow = 28;
                            }"""
    p = p.replace("if (type === 'supertrend') {", new_ui_guards + "\n                            if (type === 'supertrend') {")
    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')


# --- 4. UPGRADE MATH ENGINES (backtester.py & engine.py) ---
math_base = """                    elif name == 'williams_r':
                        hh = df['high'].rolling(window=length).max()
                        ll = df['low'].rolling(window=length).min()
                        RES = (hh - df['close']) / (hh - ll) * -100
                    elif name == 'mom':
                        RES = df['close'] - df['close'].shift(length)
                    elif name == 'hma':
                        def fast_wma(s, l):
                            w = np.arange(1, l + 1); w = w / w.sum()
                            res = np.convolve(s.fillna(0).values, w, 'valid')
                            return pd.Series(np.concatenate([np.full(l-1, np.nan), res]), index=s.index)
                        half_l, sqrt_l = int(length / 2), int(np.sqrt(length))
                        diff = 2 * fast_wma(df['close'], half_l) - fast_wma(df['close'], length)
                        RES = fast_wma(diff, sqrt_l)
                    elif name == 'tsi':
                        long_l, short_l = int(params.get('long_length', 25)), int(params.get('short_length', 13))
                        m = df['close'].diff()
                        ema1 = self.calc_tv_ema(m, long_l)
                        ema2 = self.calc_tv_ema(ema1, short_l)
                        abs_ema1 = self.calc_tv_ema(m.abs(), long_l)
                        abs_ema2 = self.calc_tv_ema(abs_ema1, short_l)
                        RES = 100 * (ema2 / abs_ema2)
                    elif name == 'uo':
                        fast, mid, slow = int(params.get('fast', 7)), int(params.get('mid', 14)), int(params.get('slow', 28))
                        bp = df['close'] - pd.concat([df['low'], df['close'].shift(1)], axis=1).min(axis=1)
                        tr = pd.concat([df['high'], df['close'].shift(1)], axis=1).max(axis=1) - pd.concat([df['low'], df['close'].shift(1)], axis=1).min(axis=1)
                        a1 = bp.rolling(fast).sum() / tr.rolling(fast).sum()
                        a2 = bp.rolling(mid).sum() / tr.rolling(mid).sum()
                        a3 = bp.rolling(slow).sum() / tr.rolling(slow).sum()
                        RES = 100 * (4 * a1 + 2 * a2 + a3) / 7\n"""

# Inject into Backtester
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()
if 'williams_r' not in b:
    bt_math = math_base.replace('RES = ', 'df[col_name] = ')
    b = b.replace("elif name == 'ema':", bt_math + "                    elif name == 'ema':")
    with open('./backtester.py', 'w') as f: f.write(b)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')

# Inject into Live Engine
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()
if 'williams_r' not in e:
    en_math = math_base.replace('RES = ', 'return ')
    e = e.replace("elif name == 'ema':", en_math + "                    elif name == 'ema':")
    with open('./engine.py', 'w') as f: f.write(e)
    os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')

print("✅ Advanced Indicators successfully embedded!")
