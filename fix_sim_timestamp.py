import os, re

print("🩹 surgically fixing the 'timestamp' error in the high-performance engine...")

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# THE FIX: We update the row object to include the timestamp from the time_arr
old_update = "row.update({'close': current_close, 'high': current_high, 'low': current_low})"
new_update = "row.update({'close': current_close, 'high': current_high, 'low': current_low, 'timestamp': current_time})"

if old_update in b:
    b = b.replace(old_update, new_update)
    with open('./backtester.py', 'w') as f:
        f.write(b)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
    print("✅ Timestamp field restored to math engine!")
else:
    print("❌ Pattern not found. Check if file was already modified.")
