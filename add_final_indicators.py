import os, re

print("📈 Injecting Final Pro Batch: PPO, StdDev, OBV, A/D, CMF...")

# --- 1. UPGRADE UI DROPDOWN (indicators.ts) ---
os.system('docker cp app-frontend-1:/app/lib/indicators.ts ./indicators.ts')
with open('./indicators.ts', 'r') as f: i = f.read()

if 'obv' not in i:
    new_inds = """  { value: 'ppo', label: 'Percentage Price Oscillator (PPO)', params:[{name: 'fast', def: 12}, {name: 'slow', def: 26}] },
  { value: 'stdev', label: 'Standard Deviation', params: [{name: 'length', def: 14}] },
  { value: 'obv', label: 'On Balance Volume (OBV)', params:[] },
  { value: 'adl', label: 'Accumulation/Distribution Line (A/D)', params:[] },
  { value: 'cmf', label: 'Chaikin Money Flow (CMF)', params: [{name: 'length', def: 20}] },\n"""
    
    i = i.replace('export const INDICATORS =[\n', 'export const INDICATORS =[\n' + new_inds)
    with open('./indicators.ts', 'w') as f: f.write(i)
    os.system('docker cp ./indicators.ts app-frontend-1:/app/lib/indicators.ts')
    print("✅ UI Dropdown updated.")

# --- 2. UPGRADE AI PROMPT (route.ts) ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

if 'obv' not in r:
    r = r.replace("'hma', 'williams_r', 'mom'", "'hma', 'williams_r', 'mom', 'stdev'")
    r = r.replace("'close', 'open', 'high', 'low', 'volume'", "'close', 'open', 'high', 'low', 'volume', 'obv', 'adl'")
    
    new_ai_params = """    - 'ppo' -> params: { "fast": 12, "slow": 26 }
    - 'cmf' -> params: { "length": 20 }\n"""
    r = r.replace("- 'macd'", new_ai_params + "    - 'macd'")
    
    with open('./route.ts', 'w') as f: f.write(r)
    os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')
    print("✅ AI Brain trained.")

# --- 3. UPGRADE UI GUARDS (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

if 'obv' not in p:
    p = p.replace("'hma','williams_r','mom'", "'hma','williams_r','mom','stdev'")
    
    new_guards = """                            if (type === 'cmf' && !params.length) params.length = 20;
                            if (type === 'ppo') {
                                if (!params.fast) params.fast = 12;
                                if (!params.slow) params.slow = 26;
                            }\n"""
    p = p.replace("if (type === 'tsi') {", new_guards + "                            if (type === 'tsi') {")
    
    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
    print("✅ UI Guards fortified.")

# --- 4. UPGRADE MATH ENGINES WITH CUSTOM INDENTATIONS ---
# For Backtester (20 spaces indentation)
bt_math = """
                    elif name == 'ppo':
                        f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                        ema_f = self.calc_tv_ema(df['close'], f)
                        ema_s = self.calc_tv_ema(df['close'], s)
                        df[col_name] = (ema_f - ema_s) / ema_s * 100
                    elif name == 'stdev':
                        df[col_name] = df['close'].rolling(window=length).std()
                    elif name == 'obv':
                        df[col_name] = pd.Series(np.where(df['close'] > df['close'].shift(1), df['volume'], np.where(df['close'] < df['close'].shift(1), -df['volume'], 0)), index=df.index).cumsum()
                    elif name == 'adl':
                        mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
                        mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
                        df[col_name] = (mfm * df['volume']).cumsum()
                    elif name == 'cmf':
                        l = int(params.get('length', 20))
                        mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
                        mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
                        mfv = mfm * df['volume']
                        res = mfv.rolling(window=l).sum() / df['volume'].rolling(window=l).sum()
                        df[col_name] = res.replace([np.inf, -np.inf], 0).fillna(0)"""

# For Engine (12 spaces indentation)
en_math = """
            elif name == 'ppo':
                f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                ema_f = self.calc_tv_ema(df['close'], f)
                ema_s = self.calc_tv_ema(df['close'], s)
                return (ema_f - ema_s) / ema_s * 100
            elif name == 'stdev':
                return df['close'].rolling(window=length).std()
            elif name == 'obv':
                return pd.Series(np.where(df['close'] > df['close'].shift(1), df['volume'], np.where(df['close'] < df['close'].shift(1), -df['volume'], 0)), index=df.index).cumsum()
            elif name == 'adl':
                mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
                mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
                return (mfm * df['volume']).cumsum()
            elif name == 'cmf':
                l = int(params.get('length', 20))
                mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
                mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
                mfv = mfm * df['volume']
                res = mfv.rolling(window=l).sum() / df['volume'].rolling(window=l).sum()
                return res.replace([np.inf, -np.inf], 0).fillna(0)"""

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()
if 'ppo' not in b:
    b = re.sub(r"(elif name == 'uo':[\s\S]*?df\[col_name\] = 100 \* \(4 \* a1 \+ 2 \* a2 \+ a3\) / 7)", r"\1" + bt_math, b)
    with open('./backtester.py', 'w') as f: f.write(b)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')

os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()
if 'ppo' not in e:
    e = re.sub(r"(elif name == 'uo':[\s\S]*?return 100 \* \(4 \* a1 \+ 2 \* a2 \+ a3\) / 7)", r"\1" + en_math, e)
    with open('./engine.py', 'w') as f: f.write(e)
    os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')

print("✅ Mathematical models safely embedded!")
