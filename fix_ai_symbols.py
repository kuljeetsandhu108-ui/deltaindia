import os, re

print("🧠 Upgrading AI Symbol Intelligence...")

# --- A. Fortify the AI Prompt in the Backend ---
os.system('docker cp app-frontend-1:/app/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

# Make the AI extremely strict about returning standard tickers instead of words
old_rule = '- "symbol": Crypto pair (e.g. BTCUSDT, ETHUSDT).'
new_rule = '- "symbol": STRICT Crypto pair ticker (e.g. "BTCUSDT"). Translate names like "Bitcoin" to "BTCUSDT". NEVER use hyphens.'
r = r.replace(old_rule, new_rule)

with open('./route.ts', 'w') as f: f.write(r)
os.system('docker cp ./route.ts app-frontend-1:/app/app/api/generate-strategy/route.ts')


# --- B. Inject the Intelligent Fuzzy Matcher into the UI ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# Target 1: Make the AI handler translate human words just in case
pattern_ai = r'if\s*\(data\.symbol\)\s*setSymbol\(data\.symbol\);'
smart_ai = """            if (data.symbol) {
                let s = data.symbol.toUpperCase();
                if (s.includes('BITCOIN')) s = 'BTCUSDT';
                if (s.includes('ETHEREUM')) s = 'ETHUSDT';
                if (s.includes('SOLANA')) s = 'SOLUSDT';
                setSymbol(s);
            }"""
p = re.sub(pattern_ai, smart_ai, p)

# Target 2: The Fuzzy Matcher that locks the symbol perfectly after the list loads
pattern_list = r'if\s*\(data\s*&&\s*data\.length\s*>\s*0\)\s*\{\s*setSymbolList\(data\);\s*if\s*\(!editId\)\s*setSymbol\(data\[0\]\);\s*\}'
smart_list = """                if (data && data.length > 0) {
                    setSymbolList(data);
                    if (!editId) {
                        setSymbol(prev => {
                            if (!prev) return data[0];
                            if (data.includes(prev)) return prev;
                            
                            // Fuzzy Match: Strip hyphens and slashes to find the exact asset
                            const clean = prev.toUpperCase().replace(/[^A-Z0-9]/gi, '');
                            const exact = data.find(s => s.replace(/[^A-Z0-9]/gi, '') === clean);
                            if (exact) return exact;
                            
                            // Fallback: If AI says "BTC", find the first BTC pair
                            const base = clean.replace('USDT', '').replace('USD', '');
                            const partial = data.find(s => s.replace(/[^A-Z0-9]/gi, '').startsWith(base));
                            return partial || data[0];
                        });
                    }
                }"""
p = re.sub(pattern_list, smart_list, p)

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ AI Symbol Intelligence successfully injected!")
