import os, re

print("🩹 surgically stabilizing React Hooks and killing the depth error...")

os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f:
    c = f.read()

# --- 1. Fix the Symbol Fetcher Loop ---
# We add a strict check to ensure data exists before attempting to set the symbol
old_fetch = r'const fetchSymbols = async \(\) => \{[\s\S]*?fetchSymbols\(\);'
stable_fetch = """const fetchSymbols = async () => {
        try {
            const res = await fetch(`https://api.algoease.com/data/symbols?broker=${broker}`);
            if (res.ok) {
                const data = await res.json();
                if (data && data.length > 0) {
                    setSymbolList(data);
                    if (!editId) {
                        // 🛡️ STABILITY GUARD: Only update if the symbol is actually missing or incorrect
                        if (!data.includes(symbol)) {
                            const clean = symbol.toUpperCase().replace(/[^A-Z0-9]/gi, '');
                            const exact = data.find((s: string) => s.replace(/[^A-Z0-9]/gi, '') === clean);
                            const nextSym = exact || data[0];
                            if (nextSym !== symbol) setSymbol(nextSym);
                        }
                    }
                }
            }
        } catch(e) {}
    };
    fetchSymbols();"""
c = re.sub(old_fetch, stable_fetch, c)

# --- 2. Fix the AI Handler to prevent multiple re-renders ---
# We ensure every setter only fires if the value is new
old_ai_apply = r'if \(data\.strategyName\) setStrategyName\(data\.strategyName\);[\s\S]*?if \(data\.endDate\) setEndDate\(data\.endDate\);'
stable_ai_apply = """if (data.strategyName && data.strategyName !== strategyName) setStrategyName(data.strategyName);
            if (data.symbol && data.symbol !== symbol) setSymbol(data.symbol);
            if (data.timeframe && data.timeframe !== timeframe) setTimeframe(data.timeframe);
            if (data.walletPct && data.walletPct !== walletPct) setWalletPct(data.walletPct);
            if (data.sl !== undefined && data.sl !== stopLoss) setStopLoss(data.sl);
            if (data.tp !== undefined && data.tp !== takeProfit) setTakeProfit(data.tp);
            if (data.tsl !== undefined && data.tsl !== tsl) setTsl(data.tsl);
            if (data.side && data.side.toUpperCase() !== side) setSide(data.side.toUpperCase());
            if (data.tradeMode && data.tradeMode.toUpperCase() !== tradeMode) setTradeMode(data.tradeMode.toUpperCase());
            if (data.startDate && data.startDate !== startDate) setStartDate(data.startDate);
            if (data.endDate && data.endDate !== endDate) setEndDate(data.endDate);"""
c = re.sub(old_ai_apply, stable_ai_apply, c)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ State guards applied! Circular logic eliminated.")
