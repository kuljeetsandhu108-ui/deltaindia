import os, re

os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# Add the maxLeverage state securely
if 'const [maxLeverage' not in p:
    p = p.replace('const [leverage, setLeverage] = useState(1);', 'const [leverage, setLeverage] = useState(1);\n  const [maxLeverage, setMaxLeverage] = useState(100);')

# Inject the smart fetcher that listens to pair/broker changes
fetch_hook = """
  useEffect(() => {
    const fetchLev = async () => {
        try {
            const res = await fetch(`${apiUrl}/data/leverage?broker=${broker}&symbol=${symbol}`);
            if (res.ok) {
                const data = await res.json();
                const mx = data.max_leverage || 1;
                setMaxLeverage(mx);
                setLeverage(prev => prev > mx ? mx : prev);
            }
        } catch (e) {}
    };
    if (symbol && broker) fetchLev();
  }, [broker, symbol]);
"""
if 'fetch(`${apiUrl}/data/leverage' not in p:
    p = p.replace('// FETCH LIVE SYMBOLS', fetch_hook + '\n  // FETCH LIVE SYMBOLS')

# Swap the free-text Input for a Dynamic Dropdown Select
pattern_ui = r'<div>\s*<div className="flex justify-between items-end mb-1">\s*<label className="block text-sm text-slate-400">Leverage \(x\)</label>[\s\S]*?</div>\s*<input type="number"[^>]+>\s*</div>'
pattern_ui_alt = r'<div>\s*<label className="block text-sm text-slate-400 mb-1">Leverage \(x\)</label>\s*<input type="number"[^>]+>\s*</div>'

dropdown_ui = """<div>
                      <div className="flex justify-between items-end mb-1">
                         <label className="block text-sm text-slate-400">Leverage (x)</label>
                         <span className="text-[10px] text-slate-500 font-mono bg-slate-900 px-2 py-0.5 rounded">Max {maxLeverage}x</span>
                      </div>
                      <select value={leverage} onChange={(e) => setLeverage(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none text-yellow-400 font-bold transition-all focus:border-yellow-500 cursor-pointer">
                          {[1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 75, 100].filter(l => l <= maxLeverage).map(l => (
                              <option key={l} value={l}>{l}x</option>
                          ))}
                      </select>
                    </div>"""

if re.search(pattern_ui, p): p = re.sub(pattern_ui, dropdown_ui, p)
elif re.search(pattern_ui_alt, p): p = re.sub(pattern_ui_alt, dropdown_ui, p)

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
