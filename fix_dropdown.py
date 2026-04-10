import re

with open('./page.tsx', 'r') as f:
    c = f.read()

# 1. Safely inject the state variables if they are missing
if 'const [maxLeverage' not in c:
    c = c.replace('const [leverage, setLeverage] = useState(1);', 'const [leverage, setLeverage] = useState(1);\n  const [maxLeverage, setMaxLeverage] = useState(100);')

# 2. Safely inject the API fetcher to get live limits (using hardcoded URL to prevent scope errors)
fetch_hook = """
  useEffect(() => {
    const fetchLev = async () => {
        try {
            const res = await fetch(`https://api.algoease.com/data/leverage?broker=${broker}&symbol=${symbol}`);
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
if 'const fetchLev' not in c:
    c = c.replace('// FETCH LIVE SYMBOLS', fetch_hook + '\n  // FETCH LIVE SYMBOLS')

# 3. The Precision Swap: Find the Leverage block and ONLY the Leverage block
pattern = r'<div>\s*(?:<div[^>]*>\s*)?<label[^>]*>Leverage \(x\)</label>[\s\S]*?(?=\s*<div>\s*<label[^>]*>% of Wallet)'

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

c = re.sub(pattern, dropdown_ui, c)

with open('./page.tsx', 'w') as f:
    f.write(c)
print("✅ Leverage Dropdown successfully injected!")
