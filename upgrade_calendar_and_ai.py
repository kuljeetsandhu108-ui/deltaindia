import os, re
from datetime import datetime

print("📅 Upgrading AI Time-Intelligence and Calendar UI...")
today = datetime.now().strftime('%Y-%m-%d')

# --- STEP 1: UPGRADE AI PROMPT (api/generate-strategy/route.ts) ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

# Instruct the AI on date parsing and defaults
date_rules = """    - "startDate": "YYYY-MM-DD" (If user mentions a time range, parse it. If NOT, default to "2021-01-01").
    - "endDate": "YYYY-MM-DD" (Default to current date: """ + today + """)."""

if '"startDate"' not in r:
    r = r.replace('- "tradeMode": "PAPER" or "LIVE".', '- "tradeMode": "PAPER" or "LIVE".\n' + date_rules)
    r = r.replace('"tradeMode": "PAPER",', '"tradeMode": "PAPER",\n      "startDate": "2021-01-01",\n      "endDate": "' + today + '",')

with open('./route.ts', 'w') as f: f.write(r)
os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')


# --- STEP 2: UPGRADE UI & CONSTRAINTS (dashboard/builder/page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# A. Add 'Calendar' to the imports if missing
if 'Calendar' not in p:
    p = p.replace('Database, TrendingUp', 'Database, TrendingUp, Calendar')

# B. Add default dates to the state so the boxes aren't empty on load
p = p.replace('const [startDate, setStartDate] = useState("");', 'const [startDate, setStartDate] = useState("2021-01-01");')
p = p.replace('const [endDate, setEndDate] = useState("");', f'const [endDate, setEndDate] = useState("{today}");')

# C. Ensure AI-generated dates update the UI state
ai_date_logic = """            if (data.tradeMode) setTradeMode(data.tradeMode.toUpperCase());
            if (data.startDate) setStartDate(data.startDate);
            if (data.endDate) setEndDate(data.endDate);"""
p = p.replace('if (data.tradeMode) setTradeMode(data.tradeMode.toUpperCase());', ai_date_logic)

# D. Redesign the Calendar UI with constraints (min/max)
# We look for the "DATE RANGE PICKER" block we added earlier
old_calendar_pattern = r'\{/\* DATE RANGE PICKER \*/\}[\s\S]*?<input type="date" value=\{endDate\}[\s\S]*?/>\s*</div>\s*</div>'

new_calendar_ui = """{/* 📅 PROFESSIONAL DATE RANGE PICKER */}
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-inner space-y-3 mt-4">
                <div className="flex items-center gap-2 text-indigo-400 mb-1">
                    <Calendar size={14} />
                    <span className="text-[10px] font-bold uppercase tracking-wider">Analysis Timeframe (2021 - Present)</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="block text-[9px] text-slate-500 uppercase font-bold mb-1 ml-1">From</label>
                        <input 
                            type="date" 
                            min="2021-01-01" 
                            max=\"""" + today + """\"
                            value={startDate} 
                            onChange={(e) => setStartDate(e.target.value)} 
                            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-xs text-white outline-none focus:border-indigo-500 transition-all cursor-pointer" 
                        />
                    </div>
                    <div>
                        <label className="block text-[9px] text-slate-500 uppercase font-bold mb-1 ml-1">To</label>
                        <input 
                            type="date" 
                            min="2021-01-01" 
                            max=\"""" + today + """\"
                            value={endDate} 
                            onChange={(e) => setEndDate(e.target.value)} 
                            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-xs text-white outline-none focus:border-indigo-500 transition-all cursor-pointer" 
                        />
                    </div>
                </div>
            </div>"""

p = re.sub(old_calendar_pattern, new_calendar_ui, p)

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ AI Time-Intelligence and Professional Calendar UI successfully deployed!")
