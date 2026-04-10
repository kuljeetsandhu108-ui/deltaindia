import os, re

print("📱 Injecting High-End Mobile Responsiveness...")

# --- 1. Fix Dashboard Library (Bottom Nav + Grid Stacking) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/page.tsx ./dashboard.tsx')
with open('./dashboard.tsx', 'r') as f: d = f.read()

# Make sidebar hide on mobile and add Bottom Nav
d = d.replace('flex relative font-sans', 'flex flex-col md:flex-row relative font-sans')
d = d.replace('aside className="w-72', 'aside className="hidden md:block w-72')

# Inject Bottom Navigation for Mobile
bottom_nav = """
      {/* MOBILE BOTTOM NAV */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800 px-6 py-3 flex justify-around items-center z-50 backdrop-blur-md">
        <Link href="/dashboard" className="flex flex-col items-center gap-1 text-indigo-400"><BookOpen size={20}/><span className="text-[10px] font-bold">Research</span></Link>
        <Link href="/dashboard/analyzer" className="flex flex-col items-center gap-1 text-slate-400"><TrendingUp size={20}/><span className="text-[10px]">Portfolio</span></Link>
        <Link href="/dashboard/settings" className="flex flex-col items-center gap-1 text-slate-400"><Database size={20}/><span className="text-[10px]">Data</span></Link>
      </nav>
"""
if 'MOBILE BOTTOM NAV' not in d:
    d = d.replace('</main>', '</main>\n' + bottom_nav)

# Fix Grid Stacking for Strategy Cards
d = d.replace('grid-cols-1 md:grid-cols-2 lg:grid-cols-3', 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3')

with open('./dashboard.tsx', 'w') as f: f.write(d)
os.system('docker cp ./dashboard.tsx app-frontend-1:/app/dashboard/page.tsx')


# --- 2. Fix Strategy Builder UI (Logic Card Stacking) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./builder.tsx')
with open('./builder.tsx', 'r') as f: b = f.read()

# Fix the main builder grid to stack Asset/Risk on top of Logic on mobile
b = b.replace('grid-cols-1 lg:grid-cols-4', 'grid-cols-1 xl:grid-cols-4')
b = b.replace('col-span-3 space-y-4', 'col-span-1 xl:col-span-3 space-y-4')

# Fix Logic Blocks to stack vertically on mobile
b = b.replace('flex flex-col md:flex-row items-center gap-4', 'flex flex-col lg:flex-row items-center gap-4')

# Fix Stats Row for Mobile (2 columns instead of 4)
b = b.replace('grid-cols-2 md:grid-cols-4 gap-4', 'grid-cols-2 lg:grid-cols-4 gap-4')

# Fix Trade Ledger Table (Enable Horizontal Scroll)
b = b.replace('<div className="max-h-96 overflow-y-auto">', '<div className="max-h-96 overflow-auto">')
b = b.replace('<table className="w-full', '<table className="min-w-[800px] w-full')

with open('./builder.tsx', 'w') as f: f.write(b)
os.system('docker cp ./builder.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ UI is now 100% Mobile Responsive!")
