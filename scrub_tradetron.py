import os

print("🧹 Scrubbing Tradetron from the UI...")

# --- 1. Dashboard Page Update ---
os.system('docker cp app-frontend-1:/app/app/dashboard/page.tsx ./dashboard.tsx')
with open('./dashboard.tsx', 'r') as f: d = f.read()

d = d.replace('Execution Engine', 'Compute Engine')
d = d.replace('Tradetron (External)', 'Pandas Quant Core')

with open('./dashboard.tsx', 'w') as f: f.write(d)
os.system('docker cp ./dashboard.tsx app-frontend-1:/app/app/dashboard/page.tsx')


# --- 2. Builder Page Update ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./builder.tsx')
with open('./builder.tsx', 'r') as f: b = f.read()

b = b.replace('🚀 Live Execution via Tradetron (Coming Soon)', '🧪 Live Execution Disabled (Research Mode)')

with open('./builder.tsx', 'w') as f: f.write(b)
os.system('docker cp ./builder.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ UI Successfully Updated to Pure Research Mode!")
