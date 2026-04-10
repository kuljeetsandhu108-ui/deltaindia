import os, re

print("Adding Smart UI Constraints for Leverage...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# The UI Block to replace
pattern_ui = r'<div>\s*<label className="block text-sm text-slate-400 mb-1">Leverage \(x\)</label>\s*<input type="number" value=\{leverage\}[^>]+>\s*</div>'

# The highly intelligent replacement block
smart_ui = """                    <div>
                      <div className="flex justify-between items-end mb-1">
                         <label className="block text-sm text-slate-400">Leverage (x)</label>
                         <span className="text-[10px] text-slate-500 font-mono bg-slate-900 px-2 py-0.5 rounded">{broker === 'COINDCX' ? 'Max 20x' : 'Max 100x'}</span>
                      </div>
                      <input type="number" min="1" max={broker === 'COINDCX' ? 20 : 100} value={leverage} onChange={(e) => {
                          let val = Number(e.target.value);
                          const maxLev = broker === 'COINDCX' ? 20 : 100;
                          if (val > maxLev) val = maxLev;
                          if (val < 1) val = 1;
                          setLeverage(val);
                      }} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none text-yellow-400 font-bold transition-all focus:border-yellow-500" />
                    </div>"""

content = re.sub(pattern_ui, smart_ui, content)

# Protect against the AI accidentally generating 200x for CoinDCX!
ai_target = 'if (data.leverage) setLeverage(data.leverage);'
ai_safe = '''if (data.leverage) {
                const maxL = (data.broker || broker) === 'COINDCX' ? 20 : 100;
                setLeverage(data.leverage > maxL ? maxL : data.leverage);
            }'''
content = content.replace(ai_target, ai_safe)

with open('./page.tsx', 'w') as f:
    f.write(content)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Smart Constraints successfully injected!")
