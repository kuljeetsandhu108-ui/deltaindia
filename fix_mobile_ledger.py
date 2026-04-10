import os, re

print("📱 Redesigning Trade Ledger for Elite Mobile Maneuverability...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# THE MASTER UI UPGRADE:
# We replace the old table with a responsive block that shows a Table on desktop 
# and beautiful Cards on mobile.

new_ledger_ui = """<div className="bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden">
                        <div className="p-4 border-b border-slate-700 font-bold flex justify-between items-center bg-slate-800/50">
                            <div className="flex items-center gap-2"><List size={18}/> Trade Ledger (IST)</div>
                            <div className="text-[10px] text-slate-500 uppercase">Showing {backtestResult.trades.length} Trades</div>
                        </div>
                        
                        {/* ⚡ SCROLLABLE CONTAINER FOR MASSIVE LISTS */}
                        <div className="max-h-[600px] overflow-y-auto overflow-x-hidden custom-scrollbar">
                            
                            {/* --- DESKTOP TABLE VIEW --- */}
                            <table className="w-full text-sm text-left hidden md:table">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-950 sticky top-0 z-10">
                                    <tr>
                                        <th className="px-6 py-3">Entry Time</th>
                                        <th className="px-6 py-3">Buy Price</th>
                                        <th className="px-6 py-3">Exit Time</th>
                                        <th className="px-6 py-3">Sell Price</th>
                                        <th className="px-6 py-3">Result</th>
                                        <th className="px-6 py-3 text-right">PnL</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {backtestResult.trades.map((t: any, i: number) => (
                                        <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4 text-slate-400 text-xs">{formatIST(t.entry_time)}</td>
                                            <td className="px-6 py-4 font-mono text-emerald-400">${formatPrice(t.entry_price)}</td>
                                            <td className="px-6 py-4 text-slate-400 text-xs">{formatIST(t.exit_time)}</td>
                                            <td className="px-6 py-4 font-mono text-red-400">${formatPrice(t.exit_price)}</td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded text-[10px] font-bold ${t.pnl > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                                    {t.reason || (t.pnl > 0 ? 'WIN' : 'LOSS')}
                                                </span>
                                            </td>
                                            <td className={`px-6 py-4 text-right font-mono font-bold ${t.pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {(t.pnl > 0 ? '+' : '') + '$' + formatPrice(t.pnl)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            {/* --- 📱 MOBILE CARD VIEW --- */}
                            <div className="md:hidden divide-y divide-slate-800">
                                {backtestResult.trades.map((t: any, i: number) => (
                                    <div key={i} className="p-4 bg-slate-900/40 space-y-3">
                                        <div className="flex justify-between items-start">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold ${t.pnl > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                                {t.reason || (t.pnl > 0 ? 'WIN' : 'LOSS')}
                                            </span>
                                            <div className={`font-mono font-bold text-lg ${t.pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {(t.pnl > 0 ? '+' : '') + '$' + formatPrice(t.pnl)}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4 text-[11px]">
                                            <div className="space-y-1">
                                                <div className="text-slate-500 uppercase font-bold">Entry</div>
                                                <div className="text-white">{formatIST(t.entry_time)}</div>
                                                <div className="text-emerald-400 font-mono">${formatPrice(t.entry_price)}</div>
                                            </div>
                                            <div className="space-y-1 border-l border-slate-800 pl-4">
                                                <div className="text-slate-500 uppercase font-bold">Exit</div>
                                                <div className="text-white">{formatIST(t.exit_time)}</div>
                                                <div className="text-red-400 font-mono">${formatPrice(t.exit_price)}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                        </div>
                    </div>"""

# Targeted Regex replacement of the old table container
pattern = r'<div className="bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden">[\s\S]*?<div className="max-h-96 overflow-auto">[\s\S]*?</table>\s*</div>\s*</div>'

c = re.sub(pattern, new_ledger_ui, c)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Mobile Trade Cards and Scroll Management successfully injected!")
