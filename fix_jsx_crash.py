import os, re

print("🩹 Repairing broken JSX tags in the UI...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# We target the entire corrupted block (from the audit check down to the chart div)
pattern = r'\{backtestResult\.metrics\.audit && \([\s\S]*?(?=<div className="h-80)'

# The perfectly formatted, bug-free UI block
clean_ui = """{backtestResult.metrics.audit && (
                        <div className="space-y-4 mb-6">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Max Drawdown</div><div className="text-lg font-bold text-red-400">{backtestResult.metrics.audit.max_drawdown}%</div></div>
                                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Sharpe Ratio</div><div className="text-lg font-bold text-white">{backtestResult.metrics.audit.sharpe_ratio} <span className="text-indigo-400 text-sm">/ {backtestResult.metrics.audit.sortino_ratio || "0"} (Sort)</span></div></div>
                                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Profit Factor</div><div className="text-lg font-bold text-emerald-400">{backtestResult.metrics.audit.profit_factor}</div></div>
                                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Expectancy</div><div className="text-lg font-bold text-white">${backtestResult.metrics.audit.expectancy}</div></div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center"><div className="text-slate-500 text-xs uppercase">Max Consecutive Losses</div><div className="text-lg font-bold text-orange-400">{backtestResult.metrics.audit.max_cons_losses} Trades</div></div>
                                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center"><div className="text-slate-500 text-xs uppercase">Avg Trade Duration</div><div className="text-lg font-bold text-blue-400">{backtestResult.metrics.audit.avg_duration}</div></div>
                            </div>
                        </div>
                    )}
                    
                    """

c = re.sub(pattern, clean_ui, c)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Broken tags cleanly replaced!")
