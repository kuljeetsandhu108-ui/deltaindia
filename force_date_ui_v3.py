import os, re

print("📅 Injecting Date Pickers (V3 Precision Method)...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# --- 1. Inject State Variables (Check if missing first) ---
if 'const [startDate, setStartDate]' not in c:
    c = c.replace('const [timeframe, setTimeframe] = useState("1h");', 
                  'const [timeframe, setTimeframe] = useState("1h");\n  const [startDate, setStartDate] = useState("");\n  const [endDate, setEndDate] = useState("");')

# --- 2. Update Payload to include dates ---
if 'startDate,' not in c:
    c = c.replace('state: "WAITING" }', 'startDate, endDate, state: "WAITING" }')

# --- 3. Inject UI (The Critical Part) ---
# We look for the "Timeframe" label, the select box, and its closing div.
# We capture the entire block so we can append to it.
target_pattern = r'(<div>\s*<label[^>]*>Timeframe</label>[\s\S]*?</select>\s*</div>)'

date_picker_ui = """
            <div className="grid grid-cols-2 gap-2 mt-4 bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                <div>
                    <label className="block text-[10px] text-slate-500 uppercase font-bold mb-1">From Date</label>
                    <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-1 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div>
                    <label className="block text-[10px] text-slate-500 uppercase font-bold mb-1">To Date</label>
                    <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-1 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
            </div>"""

if 'From Date' not in c:
    # Check if we found the target
    match = re.search(target_pattern, c)
    if match:
        print("✅ Found Timeframe block. Appending Date UI...")
        # Replace the found block with (Found Block + New UI)
        c = c.replace(match.group(0), match.group(0) + date_picker_ui)
    else:
        print("❌ CRITICAL: Could not find Timeframe block via Regex. Trying fallback anchor...")
        # Fallback: Look for the specific option tag if the div structure is weird
        c = c.replace('<option value="1d">1 Day</option>', '<option value="1d">1 Day</option></select></div>' + date_picker_ui + '<div style={{display:"none"}}><select>')

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ File updated and pushed.")
