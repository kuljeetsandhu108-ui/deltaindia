import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { prompt } = await req.json();

    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json({ error: "Gemini API key missing in .env.local" }, { status: 500 });
    }

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    
    // Low temperature ensures strict adherence to the rules
    const model = genAI.getGenerativeModel({ 
        model: "gemini-2.5-flash",
        generationConfig: {
            responseMimeType: "application/json",
            temperature: 0.1, 
        }
    });

    const systemInstruction = `You are an elite quantitative algorithmic trading assistant for 'AlgoTrade India'. 
    The user will give you a text prompt describing a trading strategy.
    You MUST output valid JSON ONLY, mapping to the platform's exact data structure.
    
    Rules for the JSON Output:
    - "strategyName": A professional name.
    - "symbol": STRICT Crypto pair ticker (e.g. "BTCUSDT"). Translate names like "Bitcoin" to "BTCUSDT". NEVER use hyphens.
    
    - "timeframe": "1m", "5m", "15m", "1h", "4h", "1d".
    - "walletPct": Number (default 10 for 10% of wallet).
    - "leverage": Number (default 1).
    - "sl": Stop loss percentage (number).
    - "tp": Take profit percentage (number).
    - "tsl": Trailing stop loss percentage (number, default 0).
    - "side": "BUY" or "SELL".
    - "tradeMode": "PAPER" or "LIVE".
    - "startDate": "YYYY-MM-DD" (If user mentions a time range, parse it. If NOT, default to "2021-01-01").
    - "endDate": "YYYY-MM-DD" (Default to current date: 2026-02-27).
    - "conditions": Array of logic conditions.

    CRITICAL OPERATOR RULES:
    - If the user explicitly mentions "cross", "crosses", "crossover", or "crossing", you MUST use the 'CROSSES_ABOVE' or 'CROSSES_BELOW' operators. Do NOT use 'GREATER_THAN' or 'LESS_THAN' for crossovers.
    - If the user says "greater than", "above" (without crossing), use 'GREATER_THAN'.
    - If the user says "less than", "below" (without crossing), use 'LESS_THAN'.

    VALID INDICATORS AND EXACT PARAMETERS REQUIRED:
    Whenever you use an indicator, you MUST include its exact params object so the engine doesn't fail.
    - 'sma', 'ema', 'wma' -> params: { "length": number }
    - 'rsi' -> params: { "length": number }
    - 'macd' -> params: { "fast": 12, "slow": 26, "sig": 9 }
    - 'bb_upper', 'bb_lower' -> params: { "length": 20, "std": 2.0 }
    - 'atr' -> params: { "length": 14 }
    - 'vwap' -> params: { "length": 14 }
    - 'adx', 'cci', 'roc' -> params: { "length": 14 }
    - 'stoch_k', 'stoch_d' -> params: { "window": 14, "smooth": 3 }
    - 'close', 'open', 'high', 'low', 'volume' -> params: {} (empty object)
    - 'number' -> params: { "value": number }
    
    JSON Structure Example:
    {
      "strategyName": "EMA Crossover",
      "symbol": "BTCUSDT",
      
      "timeframe": "15m",
      "walletPct": 10,
      "leverage": 5,
      "sl": 1.0,
      "tp": 2.0,
      "tsl": 0.5,
      "side": "BUY",
      "tradeMode": "PAPER",
      "startDate": "2021-01-01",
      "endDate": "2026-02-27",
      "conditions": [
        {
          "id": 1,
          "left": { "type": "ema", "params": { "length": 9 } },
          "operator": "CROSSES_ABOVE",
          "right": { "type": "ema", "params": { "length": 21 } }
        }
      ]
    }`;

    const finalPrompt = `${systemInstruction}

User Request: ${prompt}`;
    const result = await model.generateContent(finalPrompt);
    const responseText = result.response.text();
    
    const jsonOutput = JSON.parse(responseText);

    return NextResponse.json(jsonOutput);

  } catch (error: any) {
    console.error("AI Generation Error:", error);
    return NextResponse.json({ error: error.message || "AI Failed" }, { status: 500 });
  }
}
