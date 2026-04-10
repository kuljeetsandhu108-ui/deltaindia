import os, re

print("🩹 surgically stabilizing React Hooks to kill the infinite loop...")

os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f:
    c = f.read()

# --- STEP 1: Stabilize the Symbol Fetcher ---
# We replace the entire effect logic with a version that guards against unnecessary state updates
old_fetch_symbols = r'useEffect\(\(\) => \{[\s\S]*?fetchSymbols\(\);[\s\S]*?\}, \[broker, editId\]\);'

stable_fetch_symbols = """useEffect(() => {
    const fetchSymbols = async () => {
        try {
            setSymbolList([]); 
            const res = await fetch(`https://api.algoease.com/data/symbols?broker=${broker}`);
            if (res.ok) {
                const data = await res.json();
                if (data && data.length > 0) {
                    setSymbolList(data);
                    if (!editId) {
                        // 🛡️ STABILITY GUARD: Only set symbol if it's not already in the list
                        const currentSymbol = symbol;
                        if (!data.includes(currentSymbol)) {
                            const clean = currentSymbol.toUpperCase().replace(/[^A-Z0-9]/gi, '');
                            const exact = data.find((s: string) => s.replace(/[^A-Z0-9]/gi, '') === clean);
                            if (exact) setSymbol(exact);
                            else setSymbol(data[0]);
                        }
                    }
                }
            }
        } catch(e) {}
    };
    fetchSymbols();
  }, [broker, editId]);"""

c = re.sub(old_fetch_symbols, stable_fetch_symbols, c)

# --- STEP 2: Stabilize the Leverage Fetcher ---
# We ensure the leverage fetcher only runs when the symbol is fully ready
old_fetch_lev = r'useEffect\(\(\) => \{[\s\S]*?if \(symbol && broker\) fetchLev\(\);[\s\S]*?\}, \[broker, symbol\]\);'

stable_fetch_lev = """useEffect(() => {
    const fetchLev = async () => {
        if (!symbol || symbol === "Loading...") return;
        try {
            const res = await fetch(`https://api.algoease.com/data/leverage?broker=${broker}&symbol=${symbol}`);
            if (res.ok) {
                const data = await res.json();
                const mx = data.max_leverage || 1;
                setMaxLeverage(mx);
                // 🛡️ STABILITY GUARD: Only update leverage if it exceeds the new max
                setLeverage(prev => prev > mx ? mx : prev);
            }
        } catch (e) {}
    };
    fetchLev();
  }, [broker, symbol]);"""

c = re.sub(old_fetch_lev, stable_fetch_lev, c)

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Infinite Loop killed and hooks stabilized!")
