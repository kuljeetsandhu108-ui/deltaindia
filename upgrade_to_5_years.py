import os, re

print("🚀 Upgrading Engine for 5-Year 1-Minute Data Processing...")

# --- 1. REMOVE THE 15K SAFETY CAP IN MAIN.PY ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('main.py', 'r') as f: 
    m = f.read()

# Safely remove the fallback cap, allowing the full 5-year dataset to pass through
m = re.sub(r'elif len\(df\) > 15000:[\s\S]*?df = df\.tail\(15000\)\.reset_index\(drop=True\)', '', m)

with open('main.py', 'w') as f: 
    f.write(m)
os.system('docker cp ./main.py app-backend-1:/app/main.py')
print("✅ 15k Safety Cap Removed.")


# --- 2. UPGRADE BACKTESTER FOR HYPER-SPEED MEMORY ARRAYS ---
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('backtester.py', 'r') as f: 
    b = f.read()

# Target the slow pandas iloc loop
target_loop = r"for i in range\(1, len\(df\)\):\s*row, prev_row = df\.iloc\[i\], df\.iloc\[i-1\]"

# Replace with the hyper-fast dictionary memory array
fast_loop = """df_records = df.to_dict('records')
            
            for i in range(1, len(df_records)):
                row, prev_row = df_records[i], df_records[i-1]"""

b = re.sub(target_loop, fast_loop, b)

with open('backtester.py', 'w') as f: 
    f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ Backtester upgraded to Hyper-Speed Memory Arrays.")

