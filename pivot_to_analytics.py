import os, re

print("🛡️ Pivoting Platform to Analytics Mode (Hiding Live Execution)...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# 1. Remove the "Deploy Live" Button
# We replace it with an empty string or a "Export" placeholder later
c = re.sub(r'<button[^>]*onClick=\{handleDeploy\}[^>]*>[\s\S]*?</button>', 
           '<button className="w-full py-4 bg-slate-800 text-slate-500 cursor-not-allowed rounded-lg font-bold flex items-center justify-center gap-2 border border-slate-700">🚀 Live Execution via Tradetron (Coming Soon)</button>', c)

# 2. Remove the "Live Terminal" Modal Popup
# This prevents the black terminal box from ever appearing
c = re.sub(r'\{selectedStratId && \([\s\S]*?AnimatePresence>', '{/* Live Terminal Disabled */}\n      <AnimatePresence>', c)

# 3. Remove the "Trading Mode" (Paper/Live) Toggle
# Users don't need to select this anymore if they can't deploy live
c = re.sub(r'<div>\s*<label[^>]*>Trading Mode</label>[\s\S]*?</select>\s*</div>', '', c)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Live Execution UI successfully disabled.")
