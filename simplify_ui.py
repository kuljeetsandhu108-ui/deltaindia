import os, re

print("🎨 Streamlining UI & Restoring Save Button...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# --- 1. REMOVE BROKER DROPDOWN ---
# Find the specific div containing the Broker label and select box and erase it
pattern_broker = r'<div>\s*<label[^>]*>Broker</label>[\s\S]*?</select>\s*</div>'
c = re.sub(pattern_broker, '', c)

# Default the background state to CoinDCX so it automatically loads the 465 pairs list
c = c.replace('const [broker, setBroker] = useState("DELTA");', 'const[broker, setBroker] = useState("COINDCX");')

# --- 2. RESTORE THE SAVE BUTTON ---
# Replace the disabled "Live Execution" button with the working Save button
pattern_btn = r'<button className="[^"]*cursor-not-allowed[^"]*">🧪 Live Execution Disabled \(Research Mode\)</button>'
save_btn = '<button onClick={handleDeploy} className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-indigo-500/30"><Save size={20} /> {editId ? "Update Strategy" : "Save Strategy"}</button>'
c = re.sub(pattern_btn, save_btn, c)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ UI successfully streamlined!")
