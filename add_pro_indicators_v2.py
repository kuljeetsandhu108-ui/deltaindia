import os, re

print("📈 Injecting Pro Indicators (Supertrend, PSAR, Donchian, Keltner, Aroon)...")

# --- 1. UPGRADE UI DROPDOWN (indicators.ts) ---
os.system('docker cp app-frontend-1:/app/lib/indicators.ts ./indicators.ts')
with open('./indicators.ts', 'r') as f: i = f.read()

new_indicators = """  { value: 'supertrend', label: 'SuperTrend', params:[{name: 'length', def: 10}, {name: 'multiplier', def: 3.0}] },
  { value: 'psar', label: 'Parabolic SAR', params:[{name: 'step', def: 0.02}, {name: 'max_step', def: 0.2}] },
  { value: 'donchian_upper', label: 'Donchian Channels Upper', params:[{name: 'length', def: 20}] },
  { value: 'donchian_lower', label: 'Donchian Channels Lower', params: [{name: 'length', def: 20}] },
  { value: 'keltner_upper', label: 'Keltner Channel Upper', params:[{name: 'length', def: 20}, {name: 'multiplier', def: 2.0}] },
  { value: 'keltner_lower', label: 'Keltner Channel Lower', params:[{name: 'length', def: 20}, {name: 'multiplier', def: 2.0}] },
  { value: 'aroon_up', label: 'Aroon Up', params:[{name: 'length', def: 14}] },
  { value: 'aroon_down', label: 'Aroon Down', params:[{name: 'length', def: 14}] },\n"""

if 'supertrend' not in i:
    i = i.replace('export const INDICATORS = [', 'export const INDICATORS =[\n' + new_indicators)
    with open('./indicators.ts', 'w') as f: f.write(i)
    os.system('docker cp ./indicators.ts app-frontend-1:/app/lib/indicators.ts')


# --- 2. UPGRADE AI PROMPT (route.ts) ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

if 'supertrend' not in r:
    r = r.replace("- 'ema', 'sma', 'wma', 'rsi', 'vwap', 'atr', 'adx', 'cci', 'roc' -> params: { \"length\": number }", 
                  "- 'ema', 'sma', 'wma', 'rsi', 'vwap', 'atr', 'adx', 'cci', 'roc', 'donchian_upper', 'donchian_lower', 'aroon_up', 'aroon_down' -> params: { \"length\": number }")
    r = r.replace("- 'ema', 'sma', 'wma', 'rsi', 'adx', 'cci', 'roc', 'vwap', 'atr' -> params: { \"length\": number }", 
                  "- 'ema', 'sma', 'wma', 'rsi', 'adx', 'cci', 'roc', 'vwap', 'atr', 'donchian_upper', 'donchian_lower', 'aroon_up', 'aroon_down' -> params: { \"length\": number }")
    
    new_params = """    - 'supertrend' -> params: { "length": 10, "multiplier": 3.0 }
    - 'psar' -> params: { "step": 0.02, "max_step": 0.2 }
    - 'keltner_upper', 'keltner_lower' -> params: { "length": 20, "multiplier": 2.0 }"""
    r = r.replace('- \'macd\' -> params: { "fast": 12, "slow": 26, "sig": 9 }', 
                  '- \'macd\' -> params: { "fast": 12, "slow": 26, "sig": 9 }\n' + new_params)
    
    with open('./route.ts', 'w') as f: f.write(r)
    os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')


# --- 3. UPGRADE UI GUARDS (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

if 'supertrend' not in p:
    p = p.replace("['ema','sma','rsi','vwap','atr','adx','cci','roc']", 
                  "['ema','sma','rsi','vwap','atr','adx','cci','roc','donchian_upper','donchian_lower','aroon_up','aroon_down']")
    
    new_guards = """                            if (type === 'supertrend') {
                                if (!params.length) params.length = 10;
                                if (!params.multiplier) params.multiplier = 3.0;
                            }
                            if (type === 'psar') {
                                if (!params.step) params.step = 0.02;
                                if (!params.max_step) params.max_step = 0.2;
                            }
                            if (['keltner_upper', 'keltner_lower'].includes(type)) {
                                if (!params.length) params.length = 20;
                                if (!params.multiplier) params.multiplier = 2.0;
                            }"""
    p = p.replace("if (type === 'macd') {", new_guards + "\n                            if (type === 'macd') {")
    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')


# --- 4. UPGRADE MATH ENGINES (backtester.py & engine.py) ---
math_injection = """                    elif name == 'donchian_upper': df[col_name] = df['high'].rolling(window=length).max()
                    elif name == 'donchian_lower': df[col_name] = df['low'].rolling(window=length).min()
                    elif name == 'keltner_upper' or name == 'keltner_lower':
                        mult = float(params.get('multiplier', 2.0))
                        mid = self.calc_tv_ema(df['close'], length)
                        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                        atr = tr.rolling(window=length).mean()
                        if name == 'keltner_upper': df[col_name] = mid + (mult * atr)
                        else: df[col_name] = mid - (mult * atr)
                    elif name == 'supertrend':
                        mult = float(params.get('multiplier', 3.0))
                        hl2 = (df['high'] + df['low']) / 2
                        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                        atr = tr.rolling(window=length).mean().values
                        c_val, u_val, l_val = df['close'].values, (hl2 + mult * atr).values, (hl2 - mult * atr).values
                        st = np.zeros(len(c_val))
                        in_up = True
                        for i in range(1, len(c_val)):
                            if c_val[i] > u_val[i-1]: in_up = True
                            elif c_val[i] < l_val[i-1]: in_up = False
                            else:
                                if in_up and l_val[i] < l_val[i-1]: l_val[i] = l_val[i-1]
                                if not in_up and u_val[i] > u_val[i-1]: u_val[i] = u_val[i-1]
                            st[i] = l_val[i] if in_up else u_val[i]
                        df[col_name] = st
                    elif name == 'psar':
                        step, max_step = float(params.get('step', 0.02)), float(params.get('max_step', 0.2))
                        h_val, l_val = df['high'].values, df['low'].values
                        psar = np.zeros(len(h_val))
                        bull = True
                        af = step
                        hp, lp, ep = h_val[0], l_val[0], h_val[0]
                        psar[0] = l_val[0]
                        for i in range(1, len(h_val)):
                            psar[i] = psar[i-1] + af * (ep - psar[i-1])
                            if bull:
                                if l_val[i] < psar[i]: bull, psar[i], af, ep, lp = False, hp, step, l_val[i], l_val[i]
                                else:
                                    if h_val[i] > hp: hp, ep, af = h_val[i], h_val[i], min(af + step, max_step)
                                    if i > 1 and l_val[i-1] < psar[i]: psar[i] = l_val[i-1]
                                    if i > 2 and l_val[i-2] < psar[i]: psar[i] = l_val[i-2]
                            else:
                                if h_val[i] > psar[i]: bull, psar[i], af, ep, hp = True, lp, step, h_val[i], h_val[i]
                                else:
                                    if l_val[i] < lp: lp, ep, af = l_val[i], l_val[i], min(af + step, max_step)
                                    if i > 1 and h_val[i-1] > psar[i]: psar[i] = h_val[i-1]
                                    if i > 2 and h_val[i-2] > psar[i]: psar[i] = h_val[i-2]
                        df[col_name] = psar
                    elif name == 'aroon_up':
                        df[col_name] = df['high'].rolling(window=length+1).apply(lambda x: 100 * np.argmax(x) / length, raw=True)
                    elif name == 'aroon_down':
                        df[col_name] = df['low'].rolling(window=length+1).apply(lambda x: 100 * np.argmin(x) / length, raw=True)\n"""

for target_file in['backtester.py', 'engine.py']:
    os.system(f'docker cp app-backend-1:/app/app/{target_file} ./{target_file}')
    with open(f'./{target_file}', 'r') as f: content = f.read()
    if 'supertrend' not in content:
        content = content.replace("elif name == 'ema':", math_block + "                    elif name == 'ema':")
        with open(f'./{target_file}', 'w') as f: f.write(content)
        os.system(f'docker cp ./{target_file} app-backend-1:/app/app/{target_file}')

print("✅ Mathematical models successfully embedded!")
