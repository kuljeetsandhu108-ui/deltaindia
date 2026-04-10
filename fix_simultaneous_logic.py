import os, re

print("🎯 Injecting Simultaneous-Truth Logic & Event-Sync math...")

# --- 1. Upgrade Backtester.py (Simulations) ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

strict_logic = """            # 3. STRICT EVENT-SYNCED SIGNAL GENERATION
            entry_signals = pd.Series(True, index=df.index)
            conditions = logic.get('conditions', [])
            
            # If no conditions provided, don't generate any signals
            if not conditions:
                entry_signals = pd.Series(False, index=df.index)
            
            # Track if we have at least one "Event" (Crossover) in the strategy
            has_event = False
            event_mask = pd.Series(False, index=df.index)

            def get_series(item):
                if item['type'] == 'number': return pd.Series(float(item['params']['value']), index=df.index)
                if item['type'] in ['close', 'open', 'high', 'low', 'volume']: return df[item['type']]
                col = f"{item['type']}_{int(item['params'].get('length', 14))}"
                return df.get(col, pd.Series(0, index=df.index))
                
            for cond in conditions:
                l_s = get_series(cond['left'])
                r_s = get_series(cond['right'])
                p_l_s = l_s.shift(1).fillna(l_s)
                p_r_s = r_s.shift(1).fillna(r_s)
                op = cond['operator']
                
                # EPSILON: Professional rounding protection
                eps = 0.00000001
                
                if op == 'CROSSES_ABOVE':
                    current_cross = (l_s > r_s + eps) & (p_l_s <= p_r_s + eps)
                    event_mask = event_mask | current_cross
                    has_event = True
                elif op == 'CROSSES_BELOW':
                    current_cross = (l_s < r_s - eps) & (p_l_s >= p_r_s - eps)
                    event_mask = event_mask | current_cross
                    has_event = True
                elif op == 'GREATER_THAN':
                    entry_signals = entry_signals & (l_s > r_s + eps)
                elif op == 'LESS_THAN':
                    entry_signals = entry_signals & (l_s < r_s - eps)
                elif op == 'EQUALS':
                    entry_signals = entry_signals & (abs(l_s - r_s) < eps)

            # THE MASTER RULE:
            # If there is a crossover, the trade fires ONLY on the candle of the cross.
            # If there are only state checks (RSI > 50), it fires the moment the state becomes true.
            if has_event:
                entry_signals = entry_signals & event_mask"""

pattern_signals = r'# 3\. VECTORIZED SIGNAL GENERATION[\s\S]*?(?=\s*# 4\. LIGHTWEIGHT)'
b = re.sub(pattern_signals, strict_logic, b)

with open('./backtester.py', 'w') as f:
    f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')


# --- 2. Upgrade Engine.py (Live Awareness) ---
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')
with open('./engine.py', 'r') as f:
    e = f.read()

strict_engine_check = """    async def check_conditions(self, symbol, broker, current_price, logic):
        try:
            conditions = logic.get('conditions', [])
            if not conditions: return False
            
            df = await self.fetch_history(symbol, broker)
            if df is None or df.empty: return False
            
            # Inject current live price into the last row for real-time awareness
            df.loc[df.index[-1], 'close'] = current_price
            df = self.calculate_indicator(df, 'all_needed', logic) # Internal helper logic
            
            # Prepare Indicators
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    name, params = item.get('type'), item.get('params', {})
                    length = int(params.get('length') or 14)
                    col_name = f"{name}_{length}"
                    if col_name not in df.columns:
                        df[col_name] = self.calculate_indicator(df, name, params)

            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            has_event = False
            event_triggered = False
            all_states_true = True
            eps = 0.00000001

            def get_v(row, item):
                if item['type'] == 'number': return float(item['params']['value'])
                if item['type'] in ['close', 'open', 'high', 'low']: return float(row[item['type']])
                return float(row.get(f"{item['type']}_{int(item['params'].get('length', 14))}", 0))

            for cond in conditions:
                v_l, v_r = get_v(last, cond['left']), get_v(last, cond['right'])
                p_l, p_r = get_v(prev, cond['left']), get_v(prev, cond['right'])
                op = cond['operator']
                
                if op == 'CROSSES_ABOVE':
                    has_event = True
                    if (v_l > v_r + eps) and (p_l <= p_r + eps): event_triggered = True
                elif op == 'CROSSES_BELOW':
                    has_event = True
                    if (v_l < v_r - eps) and (p_l >= p_r - eps): event_triggered = True
                elif op == 'GREATER_THAN':
                    if not (v_l > v_r + eps): all_states_true = False
                elif op == 'LESS_THAN':
                    if not (v_l < v_r - eps): all_states_true = False
                elif op == 'EQUALS':
                    if not (abs(v_l - v_r) < eps): all_states_true = False

            if has_event:
                return event_triggered and all_states_true
            return all_states_true
        except: return False"""

pattern_engine = r'    async def check_conditions\(self, symbol, broker, current_price, logic\):[\s\S]*?except: return False'
e = re.sub(pattern_engine, strict_engine_check, e)

with open('./engine.py', 'w') as f:
    f.write(e)
os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')

print("✅ Simultaneous-Truth Aware Logic successfully deployed!")
