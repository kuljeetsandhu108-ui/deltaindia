import os, re

print("🧠 Hardening AI Value Logic and UI Numerical Guards...")

# --- STEP 1: UPGRADE AI PROMPT ---
os.system('docker cp app-frontend-1:/app/client/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

ai_strict_rule = """    - 'number' -> params: { "value": number } (CRITICAL: NEVER leave "value" blank. If comparing to MACD, use 0. If RSI, use 30, 50, or 70)."""
r = re.sub(r"- 'number' -> params: \{ \"value\": number \}", ai_strict_rule, r)

with open('./route.ts', 'w') as f: f.write(r)
os.system('docker cp ./route.ts app-frontend-1:/app/client/app/api/generate-strategy/route.ts')


# --- STEP 2: UPGRADE UI PARAMETER GUARD ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# Improved Guard Logic: Now checks specifically for the "value" property
improved_guard = """                        const fixParams = (item: any) => {
                            if (!item.params) item.params = {};
                            const p = item.params;
                            if (['ema','sma','rsi','vwap','atr','adx','cci','roc'].includes(item.type) && !p.length) p.length = 14;
                            if (item.type === 'macd') {
                                if (!p.fast) p.fast = 12;
                                if (!p.slow) p.slow = 26;
                                if (!p.sig) p.sig = 9;
                            }
                            if (item.type === 'number') {
                                // 🛡️ VALUE PROTECTION: If value is null, undefined, or empty string, force to 0
                                if (p.value === undefined || p.value === null || p.value === "") p.value = 0;
                            }
                            return item;
                        };"""

p = re.sub(r'const fixParams = \(item: any\) => \{[\s\S]*?return item;\s*\};', improved_guard, p)

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ AI Value Training and UI Logic Guard successfully hardened!")
