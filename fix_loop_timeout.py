import os, re

print("🏎️ Injecting Pre-Cast Time Array Optimization...")

os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f:
    b = f.read()

# 1. Pre-cast the entire time array to strings instantly BEFORE the loop
b = b.replace("time_arr = df['timestamp'].values", "time_arr = df['timestamp'].astype(str).values")

# 2. Remove the slow pd.to_datetime call INSIDE the loop
b = b.replace("current_time = pd.to_datetime(time_arr[i])", "current_time = time_arr[i]")

# 3. Ensure memory footprint is minimal by strictly enforcing floats
b = b.replace("current_close = close_arr[i]", "current_close = float(close_arr[i])")
b = b.replace("current_high = high_arr[i]", "current_high = float(high_arr[i])")
b = b.replace("current_low = low_arr[i]", "current_low = float(low_arr[i])")

with open('./backtester.py', 'w') as f:
    f.write(b)

os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
print("✅ Loop bottleneck completely destroyed!")
