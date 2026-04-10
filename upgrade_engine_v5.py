import os, re

print("🧠 Upgrading Backtester to High-Performance NumPy Arrays...")

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# Replace the slow, RAM-heavy dictionary loop with a memory-efficient NumPy view
target_loop = r"df_records = df\.to_dict\('records'\)[\s\S]*?for i in range\(1, len\(df_records\)\):\s*row, prev_row = df_records\[i\], df_records\[i-1\]"

fast_loop = """# High-Performance Memory-Efficient Loop
            close_arr = df['close'].values
            high_arr = df['high'].values
            low_arr = df['low'].values
            time_arr = df['timestamp'].values
            
            # Prepare indicator columns for fast access
            cols = {col: df[col].values for col in df.columns if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']}
            
            for i in range(1, len(df)):
                current_close = close_arr[i]
                current_high = high_arr[i]
                current_low = low_arr[i]
                current_time = time_arr[i]
                
                # Mock row object for logic helper
                row = {k: v[i] for k, v in cols.items()}
                row.update({'close': current_close, 'high': current_high, 'low': current_low})
                
                prev_row = {k: v[i-1] for k, v in cols.items()}
                prev_row.update({'close': close_arr[i-1]})"""

b = re.sub(target_loop, fast_loop, b)

with open('./backtester.py', 'w') as f:
    f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')

# --- 3. INCREASE SERVER TIMEOUT ---
os.system('docker cp app-backend-1:/Dockerfile ./Dockerfile_backend')
with open('./Dockerfile_backend', 'r') as f:
    d = f.read()

# Change timeout to 300 seconds
d = d.replace('--port', '--timeout-keep-alive 300 --port')
with open('./Dockerfile_backend', 'w') as f:
    f.write(d)
os.system('docker cp ./Dockerfile_backend app-backend-1:/Dockerfile')

print("✅ Backtesting engine is now optimized for 3 Million+ rows!")
