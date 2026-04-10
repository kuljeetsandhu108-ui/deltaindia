import os, re

print("🧠 Hardening AI and UI to ensure NO EMPTY VALUES...")

# --- STEP 1: UPGRADE AI PROMPT (route.ts) ---
os.system('docker cp app-frontend-1:/app/client/app/api/generate-strategy/route.ts ./route.ts')
with open('./route.ts', 'r') as f: r = f.read()

# Make the AI rules even more "Hardcore"
hardcore_rules = """    CRITICAL SCHEMA RULES:
    - EVERY 'params' object must be fully populated.
    - 'number' indicator MUST have "value": [number]. If comparing to MACD/Oscillators, this MUST be 0.
    - NEVER return null or empty strings for any parameter."""

r = re.sub(r'REQUIRED PARAMETER DICTIONARY[\s\S]*?- \'close\'', hardcore_rules + '\n\n    REQUIRED PARAMETER DICTIONARY\n    - \'close\'', r)

with open('./route.ts', 'w') as f: f.write(r)
os.system('docker cp ./route.ts app-frontend-1:/app/client/app/api/generate-strategy/route.ts')


# --- STEP 2: UPGRADE UI COMPONENT (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# 1. Fix the AI Handler mapping to be more aggressive
guard_logic = """                        const fixParams = (item: any) => {
                            const type = item.type;
                            const params = item.params || {};
                            if (['ema','sma','rsi','vwap','atr','adx','cci','roc'].includes(type) && !params.length) params.length = 14;
                            if (type === 'macd') {
                                if (!params.fast) params.fast = 12;
                                if (!params.slow) params.slow = 26;
                                if (!params.sig) params.sig = 9;
                            }
                            if (type === 'number') {
                                // 🛡️ AGGRESSIVE GUARD: If AI sends nothing, null, or empty string, set to 0
                                if (params.value === undefined || params.value === null || params.value === "") {
                                    params.value = 0;
                                } else {
                                    params.value = Number(params.value);
                                }
                            }
                            return { ...item, params };
                        };"""

p = re.sub(r'const fixParams = \(item: any\) => \{[\s\S]*?return \{ \.\.\.item, params \};\s*\};', guard_logic, p)

# 2. Fix the Input field itself to have a "Visual Fallback"
# Old: value={data.params?.[p.name] || ''}
# New: value={data.params?.[p.name] ?? (p.name === 'value' ? 0 : (p.name === 'length' ? 14 : ''))}
p = p.replace("value={data.params?.[p.name] || ''}", "value={data.params?.[p.name] ?? (p.name === 'value' ? 0 : (p.name === 'length' ? 14 : ''))}")

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ AI Schema reinforced and UI Input Fallbacks installed!")
