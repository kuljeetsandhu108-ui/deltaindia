import os
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

banner_ui = """{backtestResult.metrics.start_date && (
                        <div className="bg-indigo-900/40 border border-indigo-500/50 text-indigo-200 px-6 py-3 rounded-xl text-sm font-bold flex justify-center items-center gap-2 mb-6 shadow-lg shadow-indigo-900/20">
                            <span>📅 Certified Data Span:</span> 
                            <span className="text-white">{formatIST(backtestResult.metrics.start_date)}</span> 
                            <span className="text-indigo-400">to</span> 
                            <span className="text-white">{formatIST(backtestResult.metrics.end_date)}</span>
                        </div>
                    )}
                    <div className="h-80 w-full bg-slate-900"""

if 'Certified Data Span' not in p:
    p = p.replace('<div className="h-80 w-full bg-slate-900', banner_ui)
    with open('./page.tsx', 'w') as f: f.write(p)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
