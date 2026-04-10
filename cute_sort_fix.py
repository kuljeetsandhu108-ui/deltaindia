import os

print("🎀 Applying the Cute Sort fix (Latest Trades at top)...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# THE FIX: Remove the .slice().reverse() from the trades map
# This tells the UI to respect the backend's Newest-to-Oldest sorting
old_line = "backtestResult.trades.slice().reverse().map"
new_line = "backtestResult.trades.map"

if old_line in content:
    content = content.replace(old_line, new_line)
    with open('./page.tsx', 'w') as f:
        f.write(content)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
    print("✅ Frontend reversed! Latest trades will now appear at the top.")
else:
    print("⚠️ The line was not found. It might have already been updated.")

