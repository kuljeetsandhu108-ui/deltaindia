import os, re

print("🩹 surgically fixing the 'isoformat' error in the high-performance engine...")

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# THE FIX: We convert the numpy.datetime64 into a standard Pandas Timestamp
# This supports .isoformat() and is compatible with all our existing logic.
old_time_line = "current_time = time_arr[i]"
new_time_line = "current_time = pd.to_datetime(time_arr[i])"

if old_time_line in b:
    b = b.replace(old_time_line, new_time_line)
    
    # Also ensure the first trade timestamp comparison is robust
    b = b.replace("pd.to_datetime(t['exit_time'])", "pd.to_datetime(t['exit_time'], utc=True)")
    b = b.replace("pd.to_datetime(t['entry_time'])", "pd.to_datetime(t['entry_time'], utc=True)")

    with open('./backtester.py', 'w') as f:
        f.write(b)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
    print("✅ Timestamp formatting restored to math engine!")
else:
    print("❌ Pattern not found. Check if the loop structure is already optimized.")
