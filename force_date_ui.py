import os

print("📅 Forcing Date Picker UI into the dashboard...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# --- STEP 1: Inject State Variables (if missing) ---
if 'const [startDate, setStartDate]' not in c:
    # Find the timeframe state and add dates right after it
    c = c.replace('const [timeframe, setTimeframe] = useState("1h");', 
                  'const [timeframe, setTimeframe] = useState("1h");\n  const [startDate, setStartDate] = useState("");\n  const [endDate, setEndDate] = useState("");')

# --- STEP 2: Update the Payload to send dates to the backend ---
# We replace the logic object to ensure dates are included
if 'startDate,' not in c:
    c = c.replace('state: "WAITING" }', 'startDate, endDate, state: "WAITING" }')

# --- STEP 3: Inject the UI HTML (The missing part!) ---
# We look for the exact closing div of the Timeframe block
timeframe_close = '</select>\n            </div>'
date_ui = """</select>
            </div>
            
            {/* DATE RANGE PICKER */}
            <div className="grid grid-cols-2 gap-2 mt-4 bg-slate-950/50 p-2 rounded-lg border border-slate-800">
                <div>
                    <label className="block text-[10px] text-slate-500 uppercase font-bold mb-1">From Date</label>
                    <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div>
                    <label className="block text-[10px] text-slate-500 uppercase font-bold mb-1">To Date</label>
                    <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
            </div>"""

if 'DATE RANGE PICKER' not in c:
    # We replace the closing tag with the closing tag + the new UI
    c = c.replace(timeframe_close, date_ui)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Date UI successfully forced!")
