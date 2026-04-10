import os

print("🚑 Healing Backend API Crash...")
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')

with open('./backtester.py', 'r') as f:
    content = f.read()

# If the instantiation was accidentally swallowed, restore it!
if 'backtester = Backtester()' not in content:
    content += '\n\nbacktester = Backtester()\n'
    with open('./backtester.py', 'w') as f:
        f.write(content)
    os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
    print("✅ Restored missing Engine Object!")
else:
    print("✅ Engine Object already exists.")

