import os

print("🧠 Hardening AI Brain and Parameter Logic...")

# --- 1. UPGRADE THE AI SYSTEM INSTRUCTIONS (route.ts) ---
ai_route_path = 'client/app/api/generate-strategy/route.ts'
os.system(f'docker cp app-frontend-1:/app/{ai_route_path} ./route.ts')

new_ai_logic = """import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { prompt } = await req.json();
    if (!process.env.GEMINI_API_KEY) return NextResponse.json({ error: "API Key Missing" }, { status: 500 });

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ 
        model: "gemini-1.5-flash",
        generationConfig: { responseMimeType: "application/json", temperature: 0.1 }
    });

    const systemInstruction = `You are a Senior Quant Developer. Output VALID JSON ONLY.
    
    REQUIRED PARAMETER DICTIONARY (NEVER LEAVE EMPTY):
    - 'ema', 'sma', 'wma', 'rsi', 'adx', 'cci', 'roc', 'vwap', 'atr' -> params: { "length": number }
    - 'macd' -> params: { "fast": 12, "slow": 26, "sig": 9 }
    - 'bb_upper', 'bb_lower' -> params: { "length": 20, "std": 2.0 }
    - 'stoch_k', 'stoch_d' -> params: { "window": 14, "smooth": 3 }
    - 'number' -> params: { "value": number }
    - 'close', 'open', 'high', 'low', 'volume' -> params: {}
    
    STRICT LOGIC RULES:
    1. CROSSOVERS: If the user says "cross", "crossover", or "crossing", you MUST use 'CROSSES_ABOVE' or 'CROSSES_BELOW'. NEVER use GREATER_THAN for a cross event.
    2. TIME: If no dates mentioned, default "startDate" to "2021-01-01" and "endDate" to current.
    3. SYMBOLS: Always return strictly as "BTCUSDT", "ETHUSDT", etc. (No hyphens).
    
    Example Output:
    {
      "strategyName": "Pro Scalper",
      "symbol": "BTCUSDT",
      "broker": "COINDCX",
      "timeframe": "15m",
      "walletPct": 10,
      "leverage": 1,
      "startDate": "2021-01-01",
      "endDate": "2026-02-27",
      "side": "BUY",
      "tradeMode": "PAPER",
      "conditions": [
        { "id": 1, "left": { "type": "ema", "params": { "length": 9 } }, "operator": "CROSSES_ABOVE", "right": { "type": "ema", "params": { "length": 21 } } }
      ]
    }`;

    const result = await model.generateContent(systemInstruction + "\\n\\nUser Request: " + prompt);
    return NextResponse.json(JSON.parse(result.response.text()));
  } catch (error) { return NextResponse.json({ error: "AI Failed" }, { status: 500 }); }
}
"""

with open('./route.ts', 'w') as f: f.write(new_ai_logic)
os.system(f'docker cp ./route.ts app-frontend-1:/app/{ai_route_path}')


# --- 2. UPGRADE UI VALIDATION GUARD (page.tsx) ---
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')
with open('./page.tsx', 'r') as f: p = f.read()

# Add a safety function to ensure params are never empty in the UI
guard_code = """                if (data.conditions && data.conditions.length > 0) {
                    const mappedConds = data.conditions.map((c: any, index: number) => {
                        // 🛡️ UI PARAMETER GUARD: Auto-fill defaults if AI forgets
                        const fixParams = (item: any) => {
                            if (!item.params || Object.keys(item.params).length === 0) {
                                if (['ema','sma','rsi','vwap','atr'].includes(item.type)) item.params = { length: 14 };
                                if (item.type === 'macd') item.params = { fast: 12, slow: 26, sig: 9 };
                                if (item.type === 'number') item.params = { value: 50 };
                            }
                            return item;
                        };
                        return {
                            id: Date.now() + index,
                            left: fixParams(c.left || { type: 'close', params: {} }),
                            operator: c.operator || 'GREATER_THAN',
                            right: fixParams(c.right || { type: 'number', params: { value: 0 } })
                        };
                    });
                    setConditions(mappedConds);
                }"""

# Inject the guard into the AI response handler
import re
p = re.sub(r'if \(data\.conditions && data\.conditions\.length > 0\) \{[\s\S]*?setConditions\(mappedConds\);\s*\}', guard_code, p)

with open('./page.tsx', 'w') as f: f.write(p)
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')

print("✅ AI Brain upgraded and UI Safety Guard installed!")
