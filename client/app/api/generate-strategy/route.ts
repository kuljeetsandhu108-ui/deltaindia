import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { prompt } = await req.json();

    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json({ error: "Gemini API key missing in .env.local" }, { status: 500 });
    }

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    
    // We use gemini-1.5-flash for speed and JSON capabilities
    const model = genAI.getGenerativeModel({ 
        model: "gemini-1.5-flash",
        generationConfig: {
            responseMimeType: "application/json",
            temperature: 0.2, // Low temp for strict logic
        }
    });

    const systemInstruction = \
    You are an elite quantitative algorithmic trading assistant for 'AlgoTrade India'. 
    The user will give you a text prompt describing a trading strategy.
    You MUST output valid JSON ONLY, mapping to the platform's exact data structure.
    
    Rules for the JSON Output:
    - "strategyName": A professional name.
    - "symbol": Crypto pair (e.g. BTCUSDT, ETHUSDT).
    - "broker": "DELTA" or "COINDCX".
    - "timeframe": "1m", "5m", "15m", "1h", "4h", "1d".
    - "quantity": Number (default 1).
    - "sl": Stop loss percentage (number).
    - "tp": Take profit percentage (number).
    - "conditions": Array of logic conditions.
    
    Valid Indicator Types for 'left' or 'right':
    'rsi', 'ema', 'sma', 'macd', 'adx', 'cci', 'bb_upper', 'bb_lower', 'atr', 'close', 'open', 'high', 'low', 'volume', 'number'.
    
    Valid Operators:
    'GREATER_THAN', 'LESS_THAN', 'CROSSES_ABOVE', 'CROSSES_BELOW', 'EQUALS'.
    
    JSON Structure Example:
    {
      "strategyName": "RSI Reversal",
      "symbol": "BTCUSDT",
      "broker": "COINDCX",
      "timeframe": "5m",
      "quantity": 1,
      "sl": 1.0,
      "tp": 2.0,
      "conditions": [
        {
          "id": 1,
          "left": { "type": "rsi", "params": { "length": 14 } },
          "operator": "LESS_THAN",
          "right": { "type": "number", "params": { "value": 30 } }
        }
      ]
    }
    \;

    const finalPrompt = \\\n\nUser Request: \\;
    const result = await model.generateContent(finalPrompt);
    const responseText = result.response.text();
    
    const jsonOutput = JSON.parse(responseText);

    return NextResponse.json(jsonOutput);

  } catch (error: any) {
    console.error("AI Generation Error:", error);
    return NextResponse.json({ error: error.message || "AI Failed" }, { status: 500 });
  }
}
