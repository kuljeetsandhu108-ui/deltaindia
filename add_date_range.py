import os, re

print("📅 Injecting Calendar Date Range Selection...")

# --- 1. FRONTEND UPGRADE (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# Add State Variables for Dates
if 'const [startDate' not in p:
    p = p.replace('const [quantity, setQuantity] = useState(1);', 'const [quantity, setQuantity] = useState(1);\n  const [startDate, setStartDate] = useState("");\n  const [endDate, setEndDate] = useState("");')
    
    # Pass dates in payload
    p = p.replace('side, tradeMode, state: "WAITING"', 'side, tradeMode, startDate, endDate, state: "WAITING"')

    # Inject Date Pickers UI under Timeframe
    # We use a nice grid layout
    ui_block = """            <div>
                <label className="block text-sm text-slate-400 mb-1 flex items-center gap-2">Timeframe</label>
                <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none">
                    <option value="1m">1 Min</option>
                    <option value="5m">5 Min</option>
                    <option value="15m">15 Min</option>
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hour</option>
                    <option value="1d">1 Day</option>
                </select>
            </div>
            
            <div className="grid grid-cols-2 gap-2">
                <div>
                    <label className="block text-[10px] text-slate-500 uppercase font-bold mb-1">From Date</label>
                    <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div>
                    <label className="block text-[10px] text-slate-500 uppercase font-bold mb-1">To Date</label>
                    <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
            </div>"""
    
    # Replace the old Timeframe block with the new Timeframe + Date Picker block
    p = re.sub(r'<div>\s*<label[^>]*>Timeframe</label>\s*<select[\s\S]*?</select>\s*</div>', ui_block, p)

    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')


# --- 2. BACKEND API UPGRADE (main.py) ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: m = f.read()

# Logic: If dates exist, filter by date. If NOT, use the safety limit.
new_logic = """        if os.path.exists(vault_path):
            df = pd.read_parquet(vault_path)
            
            # 📅 DATE RANGE FILTERING
            s_date = strat.logic.get('startDate')
            e_date = strat.logic.get('endDate')
            
            if s_date and e_date:
                df = df[(df['timestamp'] >= pd.to_datetime(s_date)) & (df['timestamp'] <= pd.to_datetime(e_date) + pd.Timedelta(days=1))]
            elif len(df) > 15000:
                # Only cap data if NO date range is specified (Safety Mode)
                df = df.tail(15000).reset_index(drop=True)
        else:"""

# Replace the old logic block
target_block = r'        if os\.path\.exists\(vault_path\):\s*df = pd\.read_parquet\(vault_path\)[\s\S]*?if len\(df\) > 15000:\s*df = df\.tail\(15000\)\.reset_index\(drop=True\)\s*else:'

if 'startDate' not in m:
    m = re.sub(target_block, new_logic, m)
    with open('./main.py', 'w') as f: f.write(m)
    os.system('docker cp ./main.py app-backend-1:/app/main.py')

print("✅ Date Range & Limit Removal successfully injected!")
