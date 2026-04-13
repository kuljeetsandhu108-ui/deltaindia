import os, re

print("🚑 Healing Indentation Error & Restoring Backend...")

# ==========================================
# 1. FIX ENGINE.PY (LIVE MATH)
# ==========================================
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f: e = f.read()

perfect_engine_calc = """    def calculate_indicator(self, df, name, params):
        import pandas as pd
        import numpy as np
        try:
            length = int(params.get('length') or 14)
            if name == 'rsi':
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                return 100 - (100 / (1 + (gain / loss)))
            elif name == 'ema': return self.calc_tv_ema(df['close'], length)
            elif name == 'sma': return df['close'].rolling(window=length).mean()
            elif name == 'macd':
                f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                return self.calc_tv_ema(df['close'], f) - self.calc_tv_ema(df['close'], s)
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
            elif name == 'donchian_upper': return df['high'].rolling(window=length).max()
            elif name == 'donchian_lower': return df['low'].rolling(window=length).min()
            elif name == 'keltner_upper' or name == 'keltner_lower':
                mult = float(params.get('multiplier', 2.0))
                mid = self.calc_tv_ema(df['close'], length)
                tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(window=length).mean()
                if name == 'keltner_upper': return mid + (mult * atr)
                else: return mid - (mult * atr)
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
                return pd.Series(st, index=df.index)
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
                return pd.Series(psar, index=df.index)
            elif name == 'aroon_up': return df['high'].rolling(window=length+1).apply(lambda x: 100 * np.argmax(x) / length, raw=True)
            elif name == 'aroon_down': return df['low'].rolling(window=length+1).apply(lambda x: 100 * np.argmin(x) / length, raw=True)
            elif name == 'williams_r':
                hh = df['high'].rolling(window=length).max()
                ll = df['low'].rolling(window=length).min()
                return (hh - df['close']) / (hh - ll) * -100
            elif name == 'mom': return df['close'] - df['close'].shift(length)
            elif name == 'hma':
                half_l, sqrt_l = int(length / 2), int(np.sqrt(length))
                def wma(s, l):
                    weights = np.arange(1, l + 1)
                    return s.rolling(l).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
                diff = 2 * wma(df['close'], half_l) - wma(df['close'], length)
                return wma(diff, sqrt_l)
            elif name == 'tsi':
                long_l, short_l = int(params.get('long_length', 25)), int(params.get('short_length', 13))
                diff = df['close'].diff()
                num = self.calc_tv_ema(self.calc_tv_ema(diff, long_l), short_l)
                den = self.calc_tv_ema(self.calc_tv_ema(diff.abs(), long_l), short_l)
                return 100 * (num / den)
            elif name == 'uo':
                fast, mid, slow = int(params.get('fast', 7)), int(params.get('mid', 14)), int(params.get('slow', 28))
                prev_close = df['close'].shift(1)
                bp = df['close'] - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                tr = pd.concat([df['high'], prev_close], axis=1).max(axis=1) - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                a1 = bp.rolling(fast).sum() / tr.rolling(fast).sum()
                a2 = bp.rolling(mid).sum() / tr.rolling(mid).sum()
                a3 = bp.rolling(slow).sum() / tr.rolling(slow).sum()
                return 100 * (4 * a1 + 2 * a2 + a3) / 7
            return pd.Series(0, index=df.index)
        except Exception as e:
            print(f"Indicator Math Error: {e}")
            return pd.Series(0, index=df.index)

    async def check_conditions"""

pattern_engine = r'    def calculate_indicator\(self, df, name, params\):[\s\S]*?async def check_conditions'
e = re.sub(pattern_engine, perfect_engine_calc, e)

with open('./engine.py', 'w') as f: f.write(e)
os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')
print("✅ Engine.py surgically repaired.")


# ==========================================
# 2. FIX BACKTESTER.PY (SIMULATION MATH)
# ==========================================
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

perfect_backtest_calc = """                    if name == 'rsi':
                        delta = df['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                        df[col_name] = 100 - (100 / (1 + (gain / loss)))
                    elif name == 'ema': df[col_name] = self.calc_tv_ema(df['close'], length)
                    elif name == 'sma': df[col_name] = df['close'].rolling(window=length).mean()
                    elif name == 'macd':
                        f, s = int(params.get('fast', 12)), int(params.get('slow', 26))
                        df[col_name] = self.calc_tv_ema(df['close'], f) - self.calc_tv_ema(df['close'], s)
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
                    elif name == 'donchian_upper': df[col_name] = df['high'].rolling(window=length).max()
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
                    elif name == 'aroon_up': df[col_name] = df['high'].rolling(window=length+1).apply(lambda x: 100 * np.argmax(x) / length, raw=True)
                    elif name == 'aroon_down': df[col_name] = df['low'].rolling(window=length+1).apply(lambda x: 100 * np.argmin(x) / length, raw=True)
                    elif name == 'williams_r':
                        hh = df['high'].rolling(window=length).max()
                        ll = df['low'].rolling(window=length).min()
                        df[col_name] = (hh - df['close']) / (hh - ll) * -100
                    elif name == 'mom': df[col_name] = df['close'] - df['close'].shift(length)
                    elif name == 'hma':
                        half_l, sqrt_l = int(length / 2), int(np.sqrt(length))
                        def wma(s, l):
                            weights = np.arange(1, l + 1)
                            return s.rolling(l).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
                        diff = 2 * wma(df['close'], half_l) - wma(df['close'], length)
                        df[col_name] = wma(diff, sqrt_l)
                    elif name == 'tsi':
                        long_l, short_l = int(params.get('long_length', 25)), int(params.get('short_length', 13))
                        diff = df['close'].diff()
                        num = self.calc_tv_ema(self.calc_tv_ema(diff, long_l), short_l)
                        den = self.calc_tv_ema(self.calc_tv_ema(diff.abs(), long_l), short_l)
                        df[col_name] = 100 * (num / den)
                    elif name == 'uo':
                        fast, mid, slow = int(params.get('fast', 7)), int(params.get('mid', 14)), int(params.get('slow', 28))
                        prev_close = df['close'].shift(1)
                        bp = df['close'] - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                        tr = pd.concat([df['high'], prev_close], axis=1).max(axis=1) - pd.concat([df['low'], prev_close], axis=1).min(axis=1)
                        a1 = bp.rolling(fast).sum() / tr.rolling(fast).sum()
                        a2 = bp.rolling(mid).sum() / tr.rolling(mid).sum()
                        a3 = bp.rolling(slow).sum() / tr.rolling(slow).sum()
                        df[col_name] = 100 * (4 * a1 + 2 * a2 + a3) / 7
            df = df.replace([float('inf'), float('-inf')], float('nan'))
            return df.ffill().bfill().fillna(0)"""

pattern_backtest = r'                    if name == \'rsi\':[\s\S]*?return df\.ffill\(\)\.bfill\(\)\.fillna\(0\)'
b = re.sub(pattern_backtest, perfect_backtest_calc, b)

with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ Backtester.py surgically repaired.")

