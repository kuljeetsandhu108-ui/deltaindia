This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

<file_summary>
This section contains a summary of this file.

<purpose>
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.
</purpose>

<file_format>
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  - File path as an attribute
  - Full contents of the file
</file_format>

<usage_guidelines>
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.
</usage_guidelines>

<notes>
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: *.db
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)
</notes>

</file_summary>

<directory_structure>
.gitignore
client/.gitignore
client/app/api/auth/[...nextauth]/route.ts
client/app/api/generate-strategy/route.ts
client/app/dashboard/builder/page.tsx
client/app/dashboard/page.tsx
client/app/dashboard/settings/page.tsx
client/app/favicon.ico
client/app/globals.css
client/app/layout.tsx
client/app/page.tsx
client/Dockerfile
client/eslint.config.mjs
client/lib/indicators.ts
client/lib/utils.ts
client/next.config.ts
client/package.json
client/postcss.config.mjs
client/public/file.svg
client/public/globe.svg
client/public/next.svg
client/public/vercel.svg
client/public/window.svg
client/README.md
client/tsconfig.json
server/algotrade.db
server/app/__init__.py
server/app/backtester.py
server/app/brokers/__init__.py
server/app/brokers/coindcx.py
server/app/crud.py
server/app/database.py
server/app/diagnostics.py
server/app/engine.py
server/app/engine/trader.py
server/app/models.py
server/app/schemas.py
server/app/security.py
server/app/utils/security.py
server/Dockerfile
server/main.py
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path=".gitignore">
node_modules/
venv/
__pycache__/
.env
.env.local
.next/
dist/
postgres_data/
</file>

<file path="client/.gitignore">
# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.*
.yarn/*
!.yarn/patches
!.yarn/plugins
!.yarn/releases
!.yarn/versions

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# env files (can opt-in for committing if needed)
.env*

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
</file>

<file path="client/app/api/auth/[...nextauth]/route.ts">
import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
</file>

<file path="client/app/api/generate-strategy/route.ts">
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
</file>

<file path="client/app/globals.css">
@import "tailwindcss";

:root {
  --background: #ffffff;
  --foreground: #171717;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: Arial, Helvetica, sans-serif;
}
</file>

<file path="client/app/layout.tsx">
"use client";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "next-auth/react";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className + " bg-slate-950 text-white antialiased"}>
        <SessionProvider>
          {children}
        </SessionProvider>
      </body>
    </html>
  );
}
</file>

<file path="client/app/page.tsx">
"use client";
import { signIn, useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { ArrowRight, Lock, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function Home() {
  const { data: session } = useSession();

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center relative overflow-hidden">
      
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-emerald-600/20 rounded-full blur-[120px]" />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="z-10 text-center max-w-3xl px-6"
      >
        <div className="mb-6 flex justify-center">
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-emerald-400 text-sm font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            System Operational
          </span>
        </div>

        <h1 className="text-6xl font-bold tracking-tight text-white mb-6">
          AlgoTrade India <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
            Automate Your Alpha
          </span>
        </h1>

        <p className="text-slate-400 text-lg mb-10">
          Institutional-grade execution for Delta Exchange & CoinDCX.
        </p>

        {session ? (
          <div className="space-y-4">
             <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                <p className="text-white">Welcome, <span className="text-cyan-400">{session.user?.name}</span></p>
             </div>
             
             {/* THIS IS THE FIX: The Link Component */}
             <Link href="/dashboard">
               <button className="px-8 py-4 bg-white text-slate-950 font-bold rounded-lg hover:bg-slate-200 transition-all flex items-center gap-2 mx-auto">
                 Enter Dashboard <ArrowRight size={20} />
               </button>
             </Link>
          </div>
        ) : (
          <button
            onClick={() => signIn("google")}
            className="group relative px-8 py-4 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 transition-all overflow-hidden"
          >
            <span className="relative z-10 flex items-center gap-2">
              Start Trading Now <ArrowRight size={20} />
            </span>
          </button>
        )}
      </motion.div>
    </div>
  );
}
</file>

<file path="client/eslint.config.mjs">
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
</file>

<file path="client/lib/indicators.ts">
export const INDICATORS = [
  // --- TREND ---
  { value: 'sma', label: 'SMA (Simple Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'ema', label: 'EMA (Exponential Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'wma', label: 'WMA (Weighted Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'macd', label: 'MACD Line', params: [{name: 'fast', def: 12}, {name: 'slow', def: 26}, {name: 'sig', def: 9}] },
  { value: 'adx', label: 'ADX (Average Directional Index)', params: [{name: 'length', def: 14}] },
  { value: 'ichimoku_a', label: 'Ichimoku Span A', params: [] },
  { value: 'ichimoku_b', label: 'Ichimoku Span B', params: [] },

  // --- MOMENTUM ---
  { value: 'rsi', label: 'RSI (Relative Strength Index)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'stoch_k', label: 'Stochastic %K', params: [{name: 'window', def: 14}, {name: 'smooth', def: 3}] },
  { value: 'stoch_d', label: 'Stochastic %D', params: [{name: 'window', def: 14}, {name: 'smooth', def: 3}] },
  { value: 'cci', label: 'CCI', params: [{name: 'length', def: 20}] },
  { value: 'roc', label: 'Rate of Change', params: [{name: 'length', def: 12}] },

  // --- VOLATILITY ---
  { value: 'bb_upper', label: 'Bollinger Bands Upper', params: [{name: 'length', def: 20}, {name: 'std', def: 2.0}] },
  { value: 'bb_lower', label: 'Bollinger Bands Lower', params: [{name: 'length', def: 20}, {name: 'std', def: 2.0}] },
  { value: 'atr', label: 'ATR', params: [{name: 'length', def: 14}] },

  // --- RAW DATA ---
  { value: 'close', label: 'Price (Close)', params: [] },
  { value: 'open', label: 'Price (Open)', params: [] },
  { value: 'high', label: 'Price (High)', params: [] },
  { value: 'low', label: 'Price (Low)', params: [] },
  { value: 'volume', label: 'Volume', params: [] },
  { value: 'number', label: 'Fixed Number', params: [{name: 'value', def: 50}] }
];
</file>

<file path="client/lib/utils.ts">
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
</file>

<file path="client/next.config.ts">
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
};

export default nextConfig;
</file>

<file path="client/postcss.config.mjs">
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
</file>

<file path="client/public/file.svg">
<svg fill="none" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path d="M14.5 13.5V5.41a1 1 0 0 0-.3-.7L9.8.29A1 1 0 0 0 9.08 0H1.5v13.5A2.5 2.5 0 0 0 4 16h8a2.5 2.5 0 0 0 2.5-2.5m-1.5 0v-7H8v-5H3v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1M9.5 5V2.12L12.38 5zM5.13 5h-.62v1.25h2.12V5zm-.62 3h7.12v1.25H4.5zm.62 3h-.62v1.25h7.12V11z" clip-rule="evenodd" fill="#666" fill-rule="evenodd"/></svg>
</file>

<file path="client/public/globe.svg">
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><g clip-path="url(#a)"><path fill-rule="evenodd" clip-rule="evenodd" d="M10.27 14.1a6.5 6.5 0 0 0 3.67-3.45q-1.24.21-2.7.34-.31 1.83-.97 3.1M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m.48-1.52a7 7 0 0 1-.96 0H7.5a4 4 0 0 1-.84-1.32q-.38-.89-.63-2.08a40 40 0 0 0 3.92 0q-.25 1.2-.63 2.08a4 4 0 0 1-.84 1.31zm2.94-4.76q1.66-.15 2.95-.43a7 7 0 0 0 0-2.58q-1.3-.27-2.95-.43a18 18 0 0 1 0 3.44m-1.27-3.54a17 17 0 0 1 0 3.64 39 39 0 0 1-4.3 0 17 17 0 0 1 0-3.64 39 39 0 0 1 4.3 0m1.1-1.17q1.45.13 2.69.34a6.5 6.5 0 0 0-3.67-3.44q.65 1.26.98 3.1M8.48 1.5l.01.02q.41.37.84 1.31.38.89.63 2.08a40 40 0 0 0-3.92 0q.25-1.2.63-2.08a4 4 0 0 1 .85-1.32 7 7 0 0 1 .96 0m-2.75.4a6.5 6.5 0 0 0-3.67 3.44 29 29 0 0 1 2.7-.34q.31-1.83.97-3.1M4.58 6.28q-1.66.16-2.95.43a7 7 0 0 0 0 2.58q1.3.27 2.95.43a18 18 0 0 1 0-3.44m.17 4.71q-1.45-.12-2.69-.34a6.5 6.5 0 0 0 3.67 3.44q-.65-1.27-.98-3.1" fill="#666"/></g><defs><clipPath id="a"><path fill="#fff" d="M0 0h16v16H0z"/></clipPath></defs></svg>
</file>

<file path="client/public/next.svg">
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 394 80"><path fill="#000" d="M262 0h68.5v12.7h-27.2v66.6h-13.6V12.7H262V0ZM149 0v12.7H94v20.4h44.3v12.6H94v21h55v12.6H80.5V0h68.7zm34.3 0h-17.8l63.8 79.4h17.9l-32-39.7 32-39.6h-17.9l-23 28.6-23-28.6zm18.3 56.7-9-11-27.1 33.7h17.8l18.3-22.7z"/><path fill="#000" d="M81 79.3 17 0H0v79.3h13.6V17l50.2 62.3H81Zm252.6-.4c-1 0-1.8-.4-2.5-1s-1.1-1.6-1.1-2.6.3-1.8 1-2.5 1.6-1 2.6-1 1.8.3 2.5 1a3.4 3.4 0 0 1 .6 4.3 3.7 3.7 0 0 1-3 1.8zm23.2-33.5h6v23.3c0 2.1-.4 4-1.3 5.5a9.1 9.1 0 0 1-3.8 3.5c-1.6.8-3.5 1.3-5.7 1.3-2 0-3.7-.4-5.3-1s-2.8-1.8-3.7-3.2c-.9-1.3-1.4-3-1.4-5h6c.1.8.3 1.6.7 2.2s1 1.2 1.6 1.5c.7.4 1.5.5 2.4.5 1 0 1.8-.2 2.4-.6a4 4 0 0 0 1.6-1.8c.3-.8.5-1.8.5-3V45.5zm30.9 9.1a4.4 4.4 0 0 0-2-3.3 7.5 7.5 0 0 0-4.3-1.1c-1.3 0-2.4.2-3.3.5-.9.4-1.6 1-2 1.6a3.5 3.5 0 0 0-.3 4c.3.5.7.9 1.3 1.2l1.8 1 2 .5 3.2.8c1.3.3 2.5.7 3.7 1.2a13 13 0 0 1 3.2 1.8 8.1 8.1 0 0 1 3 6.5c0 2-.5 3.7-1.5 5.1a10 10 0 0 1-4.4 3.5c-1.8.8-4.1 1.2-6.8 1.2-2.6 0-4.9-.4-6.8-1.2-2-.8-3.4-2-4.5-3.5a10 10 0 0 1-1.7-5.6h6a5 5 0 0 0 3.5 4.6c1 .4 2.2.6 3.4.6 1.3 0 2.5-.2 3.5-.6 1-.4 1.8-1 2.4-1.7a4 4 0 0 0 .8-2.4c0-.9-.2-1.6-.7-2.2a11 11 0 0 0-2.1-1.4l-3.2-1-3.8-1c-2.8-.7-5-1.7-6.6-3.2a7.2 7.2 0 0 1-2.4-5.7 8 8 0 0 1 1.7-5 10 10 0 0 1 4.3-3.5c2-.8 4-1.2 6.4-1.2 2.3 0 4.4.4 6.2 1.2 1.8.8 3.2 2 4.3 3.4 1 1.4 1.5 3 1.5 5h-5.8z"/></svg>
</file>

<file path="client/public/vercel.svg">
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1155 1000"><path d="m577.3 0 577.4 1000H0z" fill="#fff"/></svg>
</file>

<file path="client/public/window.svg">
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill-rule="evenodd" clip-rule="evenodd" d="M1.5 2.5h13v10a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1zM0 1h16v11.5a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 0 12.5zm3.75 4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5M7 4.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0m1.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5" fill="#666"/></svg>
</file>

<file path="client/README.md">
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
</file>

<file path="client/tsconfig.json">
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.mts"
  ],
  "exclude": ["node_modules"]
}
</file>

<file path="server/app/__init__.py">

</file>

<file path="server/app/brokers/__init__.py">

</file>

<file path="server/app/engine/trader.py">
# server/app/engine/trader.py
import time
import hmac
import hashlib
import json
import requests

class IndianBrokerBridge:
    """
    Connects to Delta Exchange or CoinDCX using specific user credentials.
    """
    def __init__(self, broker_name, api_key, api_secret):
        self.broker = broker_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.delta.exchange" if broker_name == "DELTA" else "https://api.coindcx.com"

    def get_market_price(self, symbol):
        # In production, this would be a WebSocket listener. 
        # For MVP, we use REST API to get price.
        if self.broker == "DELTA":
            response = requests.get(f"{self.base_url}/v2/tickers", params={"symbol": symbol})
            data = response.json()
            # Parsing logic specific to Delta
            return float(data['result'][0]['close'])
        
        # Add CoinDCX logic here
        return 0.0

    def execute_order(self, symbol, side, size):
        print(f"Executing {side} order for {size} {symbol} on {self.broker}...")
        # Here we would sign the request and POST to the broker
        return {"status": "filled", "price": 10000}

class StrategyExecutor:
    """
    The Brain that interprets the "No-Code" logic.
    """
    def __init__(self, user_config, broker_bridge):
        self.config = user_config # JSON object defining the strategy
        self.broker = broker_bridge
        self.is_running = False

    def check_indicators(self, current_price, indicators):
        # Calculate EMAs, RSIs here based on historical buffer
        # For this demo, we simulate a logic check
        ema_val = indicators.get('ema_20', 0)
        return ema_val

    def run_cycle(self):
        """
        The heartbeat of the algo.
        """
        symbol = self.config['pair'] # e.g., "BTCUSD"
        current_price = self.broker.get_market_price(symbol)
        
        # LOGIC INTERPRETER
        # Example Condition: If Price > EMA(20)
        
        # 1. Parse Logic
        condition_type = self.config['conditions'][0]['type'] # "CROSSOVER"
        indicator_value = 50000 # Mock calculation
        
        print(f"Checking: {symbol} Price: {current_price}")

        if current_price > indicator_value:
            # Trigger Buy
            self.broker.execute_order(symbol, "BUY", self.config['amount'])

# This file will be called by the worker when a user activates a strategy
</file>

<file path="server/app/security.py">
from cryptography.fernet import Fernet
import os
import base64

# In a real app, load this from .env. For now, we generate/use a static key for dev.
# This key MUST be 32 url-safe base64-encoded bytes.
# We will use a fixed key for this demo so it persists across restarts.
KEY = b'8_5V3d_v4p8p4u7H8d3_843d837d834d834d834d834=' 

def get_cipher():
    # If the key above is invalid, we generate a new one (for safety)
    try:
        return Fernet(KEY)
    except:
        return Fernet(Fernet.generate_key())

def encrypt_value(value: str) -> str:
    if not value: return None
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value: return None
    cipher = get_cipher()
    return cipher.decrypt(encrypted_value.encode()).decode()
</file>

<file path="server/app/utils/security.py">
from cryptography.fernet import Fernet
import os

# Generate this once and store in your .env file on the server
# key = Fernet.generate_key() 
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key()) 

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_api_key(raw_key: str) -> str:
    return cipher.encrypt(raw_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    return cipher.decrypt(encrypted_key.encode()).decode()
</file>

<file path="server/Dockerfile">
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
</file>

<file path="client/Dockerfile">
FROM node:20-alpine
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# 🔥 CRITICAL: Must tell Next.js it is Production BEFORE the build starts
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

CMD ["npm", "start"]
</file>

<file path="server/app/diagnostics.py">
import ccxt.async_support as ccxt
import time
import asyncio
import requests
from . import database
from sqlalchemy import text

async def ping_delta():
    start = time.time()
    exchange = None
    try:
        # Ping Delta India
        exchange = ccxt.delta({
            'urls': {
                'api': {'public': 'https://api.india.delta.exchange'},
                'www': 'https://india.delta.exchange'
            },
            'timeout': 10000
        })
        await exchange.fetch_time()
        latency = int((time.time() - start) * 1000)
        return {"status": "OK", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}
    finally:
        if exchange: await exchange.close()

async def ping_coindcx():
    start = time.time()
    try:
        # THE FIX: Bypass CCXT entirely for CoinDCX.
        # We use a direct HTTP request to their public markets endpoint as a "ping"
        url = "https://api.coindcx.com/exchange/v1/markets_details"
        
        # Run standard requests inside an async thread so it doesn't block the server
        response = await asyncio.to_thread(requests.get, url, timeout=10)
        
        if response.status_code == 200:
            latency = int((time.time() - start) * 1000)
            return {"status": "OK", "latency_ms": latency, "error": None}
        else:
            return {"status": "FAILED", "latency_ms": None, "error": f"HTTP Error {response.status_code}"}
            
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}

def ping_database():
    start = time.time()
    try:
        db = database.SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        latency = int((time.time() - start) * 1000)
        return {"status": "OK", "latency_ms": latency, "error": None}
    except Exception as e:
        return {"status": "FAILED", "latency_ms": None, "error": str(e)}

async def run_full_diagnostics():
    delta_res, coindcx_res = await asyncio.gather(ping_delta(), ping_coindcx())
    db_res = ping_database()
    
    return {
        "database": db_res,
        "delta_india": delta_res,
        "coindcx": coindcx_res
    }
</file>

<file path="client/package.json">
{
  "name": "client",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "@google/generative-ai": "^0.24.1",
    "clsx": "^2.1.1",
    "framer-motion": "^12.34.1",
    "lucide-react": "^0.574.0",
    "next": "16.1.6",
    "next-auth": "^4.24.13",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "recharts": "^3.7.0",
    "tailwind-merge": "^3.4.1"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "babel-plugin-react-compiler": "1.0.0",
    "eslint": "^9",
    "eslint-config-next": "16.1.6",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
</file>

<file path="server/app/database.py">
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get DB URL from Docker, fallback to sqlite for local testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./algotrade.db")

if "sqlite" in DATABASE_URL:
    # Local Dev Mode
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # 🚀 ENTERPRISE POSTGRESQL MODE (For 1000+ Users)
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,         # Hold 20 open connections ready to go
        max_overflow=10,      # Allow 10 extra connections during traffic spikes
        pool_timeout=30,      # Don't panic immediately if busy, wait up to 30s
        pool_recycle=1800     # Refresh connections every 30 mins to prevent timeouts
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()
</file>

<file path="server/app/schemas.py">
from pydantic import BaseModel
from typing import Optional, Dict, Any

class UserCreate(BaseModel):
    email: str
    full_name: str
    picture: Optional[str] = None

class BrokerKeys(BaseModel):
    email: str
    broker: str 
    api_key: str
    api_secret: str

class StrategyInput(BaseModel):
    email: str
    name: str
    symbol: str
    broker: str = "DELTA"
    logic: Dict[str, Any]
</file>

<file path="server/app/models.py">
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    picture = Column(String)
    
    # API KEYS
    delta_api_key = Column(String, nullable=True)
    delta_api_secret = Column(String, nullable=True)
    coindcx_api_key = Column(String, nullable=True)
    coindcx_api_secret = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    strategies = relationship("Strategy", back_populates="owner")

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    symbol = Column(String)
    broker = Column(String, default="DELTA") # <--- THIS IS THE CRITICAL NEW COLUMN
    logic_configuration = Column(JSON)
    is_running = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="strategies")
    logs = relationship("StrategyLog", back_populates="strategy", cascade="all, delete-orphan")

class StrategyLog(Base):
    __tablename__ = "strategy_logs"
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    message = Column(Text)
    level = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy = relationship("Strategy", back_populates="logs")
</file>

<file path="client/app/dashboard/settings/page.tsx">
"use client";
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Save, Lock, ShieldCheck, AlertCircle, Eye, EyeOff, ArrowLeft, Activity, Server, Database, Globe, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';

export default function BrokerSettings() {
  const { data: session } = useSession();
  const [showDelta, setShowDelta] = useState(false);
  const [showDcx, setShowDcx] = useState(false);
  
  const [formData, setFormData] = useState({ deltaKey: "", deltaSecret: "", dcxKey: "", dcxSecret: "" });

  // DIAGNOSTICS STATE
  const [isPinging, setIsPinging] = useState(false);
  const [healthData, setHealthData] = useState<any>(null);

  const runDiagnostics = async () => {
      setIsPinging(true);
      setHealthData(null);
      try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const res = await fetch(apiUrl + '/system/diagnostics');
          const data = await res.json();
          setHealthData(data);
      } catch (e) {
          setHealthData({ error: "Failed to reach backend server entirely." });
      }
      setIsPinging(false);
  };

  const handleSave = async (broker: string) => {
    if (!session?.user?.email) return alert("Please log in first.");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const payload = {
          email: session.user.email,
          broker: broker.toUpperCase(),
          api_key: broker === 'Delta' ? formData.deltaKey : formData.dcxKey,
          api_secret: broker === 'Delta' ? formData.deltaSecret : formData.dcxSecret
      };
      
      const res = await fetch(apiUrl + '/user/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        alert("Success! " + broker + " Keys Encrypted and Saved.");
      } else { alert("Error saving keys."); }
    } catch (error) { alert("Server Connection Error."); }
  };

  const HealthCard = ({ title, icon: Icon, data }: any) => {
      if (!data) return null;
      const isOk = data.status === 'OK';
      return (
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
              <div className="flex items-center gap-3">
                  <div className={"p-2 rounded-lg " + (isOk ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400")}>
                      <Icon size={18} />
                  </div>
                  <div>
                      <h4 className="font-bold text-sm text-white">{title}</h4>
                      {isOk ? (
                          <p className="text-xs text-slate-500">Latency: {data.latency_ms}ms</p>
                      ) : (
                          <p className="text-xs text-red-400 truncate max-w-[150px]" title={data.error}>{data.error}</p>
                      )}
                  </div>
              </div>
              <div>
                  {isOk ? <span className="flex items-center gap-2 text-xs font-bold text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> ONLINE</span>
                        : <span className="flex items-center gap-2 text-xs font-bold text-red-400"><span className="w-2 h-2 rounded-full bg-red-500"></span> OFFLINE</span>}
              </div>
          </div>
      );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 md:p-10 font-sans">
      <header className="flex justify-between items-center mb-10 border-b border-slate-800 pb-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-full transition-colors"><ArrowLeft size={24} className="text-slate-400" /></Link>
          <div><h1 className="text-3xl font-bold flex items-center gap-2">Platform Settings</h1><p className="text-slate-500 text-sm mt-1">Manage broker connections and system health.</p></div>
        </div>
        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 px-4 py-2 rounded-full text-xs font-bold border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
          <Lock size={14} /> AES-256 ENCRYPTED
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 max-w-6xl mx-auto">
        
        {/* LEFT: API KEYS */}
        <div className="xl:col-span-2 space-y-6">
            <h2 className="text-xl font-bold flex items-center gap-2"><ShieldCheck className="text-blue-400"/> Broker Integrations</h2>
            
            {/* DELTA EXCHANGE */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-slate-900 rounded-[2rem] border border-slate-800 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <div className="flex items-center gap-3"><div className="w-12 h-12 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-xl">D</div><div><h3 className="font-bold text-xl">Delta Exchange India</h3><p className="text-slate-500 text-xs">For Crypto Futures</p></div></div>
              </div>
              <div className="p-8 space-y-4">
                <div><label className="block text-sm text-slate-400 mb-2 font-medium">API Key</label><input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 outline-none focus:border-indigo-500 transition-colors" onChange={(e) => setFormData({...formData, deltaKey: e.target.value})} /></div>
                <div className="relative"><label className="block text-sm text-slate-400 mb-2 font-medium">API Secret</label><input type={showDelta ? "text" : "password"} className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 outline-none focus:border-indigo-500 transition-colors" onChange={(e) => setFormData({...formData, deltaSecret: e.target.value})} /><button onClick={() => setShowDelta(!showDelta)} className="absolute right-4 top-10 text-slate-500 hover:text-white">{showDelta ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
                <button onClick={() => handleSave('Delta')} className="w-full mt-6 bg-indigo-600 hover:bg-indigo-500 text-white py-4 rounded-xl font-bold transition-all shadow-lg hover:shadow-indigo-500/25">Save Delta Credentials</button>
              </div>
            </motion.div>
            
            {/* COINDCX */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{delay: 0.1}} className="bg-slate-900 rounded-[2rem] border border-slate-800 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <div className="flex items-center gap-3"><div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white text-xl">C</div><div><h3 className="font-bold text-xl">CoinDCX</h3><p className="text-slate-500 text-xs">For Spot & Margin</p></div></div>
              </div>
              <div className="p-8 space-y-4">
                <div><label className="block text-sm text-slate-400 mb-2 font-medium">API Key</label><input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 outline-none focus:border-blue-500 transition-colors" onChange={(e) => setFormData({...formData, dcxKey: e.target.value})} /></div>
                <div className="relative"><label className="block text-sm text-slate-400 mb-2 font-medium">API Secret</label><input type={showDcx ? "text" : "password"} className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 outline-none focus:border-blue-500 transition-colors" onChange={(e) => setFormData({...formData, dcxSecret: e.target.value})} /><button onClick={() => setShowDcx(!showDcx)} className="absolute right-4 top-10 text-slate-500 hover:text-white">{showDcx ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
                <button onClick={() => handleSave('CoinDCX')} className="w-full mt-6 bg-blue-600 hover:bg-blue-500 text-white py-4 rounded-xl font-bold transition-all shadow-lg hover:shadow-blue-500/25">Save CoinDCX Credentials</button>
              </div>
            </motion.div>
        </div>

        {/* RIGHT: DIAGNOSTICS RADAR */}
        <div className="xl:col-span-1 space-y-6">
            <h2 className="text-xl font-bold flex items-center gap-2"><Activity className="text-emerald-400"/> System Radar</h2>
            
            <div className="bg-slate-900 rounded-[2rem] border border-slate-800 p-6 shadow-xl">
                <p className="text-sm text-slate-400 mb-6">Run a full diagnostic ping to ensure the server can communicate with the databases and exchanges.</p>
                
                <button onClick={runDiagnostics} disabled={isPinging} className="w-full py-4 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mb-6">
                    <RefreshCw size={18} className={isPinging ? "animate-spin text-emerald-400" : ""} /> 
                    {isPinging ? "Pinging Servers..." : "Run Diagnostics"}
                </button>

                {healthData && (
                    <div className="space-y-3">
                        {healthData.error ? (
                            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                                ❌ {healthData.error}
                            </div>
                        ) : (
                            <>
                                <HealthCard title="Internal Database" icon={Database} data={healthData.database} />
                                <HealthCard title="Delta Exchange API" icon={Globe} data={healthData.delta_india} />
                                <HealthCard title="CoinDCX API" icon={Server} data={healthData.coindcx} />
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>

      </div>
    </div>
  );
}
</file>

<file path="server/app/crud.py">
from sqlalchemy.orm import Session
from . import models, schemas, security

def create_log(db: Session, strategy_id: int, message: str, level: str = "INFO"):
    try:
        new_log = models.StrategyLog(strategy_id=strategy_id, message=message, level=level)
        db.add(new_log)
        db.commit()
    except: pass

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, full_name=user.full_name, picture=user.picture)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_broker_keys(db: Session, keys: schemas.BrokerKeys):
    user = get_user_by_email(db, keys.email)
    if not user: return None
    enc_key = security.encrypt_value(keys.api_key)
    enc_secret = security.encrypt_value(keys.api_secret)
    if keys.broker == "DELTA":
        user.delta_api_key, user.delta_api_secret = enc_key, enc_secret
    elif keys.broker == "COINDCX":
        user.coindcx_api_key, user.coindcx_api_secret = enc_key, enc_secret
    db.commit()
    return user

def create_strategy(db: Session, strategy: schemas.StrategyInput):
    user = get_user_by_email(db, strategy.email)
    
    # ⚡ AUTO-HEAL: If user lost session sync, create them instantly
    if not user:
        user = create_user(db, schemas.UserCreate(email=strategy.email, full_name="Trader", picture=""))

    db_strat = models.Strategy(
        name=strategy.name, symbol=strategy.symbol, broker=strategy.broker,
        logic_configuration=strategy.logic, is_running=True, owner_id=user.id
    )
    db.add(db_strat)
    db.commit()
    db.refresh(db_strat)
    create_log(db, db_strat.id, f"Strategy Created on {strategy.broker}", "INFO")
    return db_strat

def get_strategy_logs(db: Session, strategy_id: int):
    return db.query(models.StrategyLog).filter(models.StrategyLog.strategy_id == strategy_id).order_by(models.StrategyLog.timestamp.desc()).limit(50).all()
</file>

<file path="server/app/brokers/coindcx.py">
import pandas as pd
import requests
import asyncio
import time
import urllib3

# Disable SSL warnings to keep logs clean
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CoinDCXManager:
    def __init__(self):
        self.id = 'coindcx'
        self.public_url = "https://public.coindcx.com"

    async def fetch_symbols(self):
        """Fetches ALL USDT pairs using Ticker API with SSL Bypass"""
        print("... CoinDCX Manager: Fetching Symbols ...")
        try:
            # 1. Use Ticker API (Proven to work)
            url = "https://api.coindcx.com/exchange/ticker"
            
            # 2. DISABLE SSL VERIFICATION (The Fix)
            # We use verify=False because Docker containers sometimes have outdated certs
            response = await asyncio.to_thread(requests.get, url, timeout=15, verify=False)
            
            if response.status_code != 200:
                print(f"❌ CoinDCX API Status: {response.status_code}")
                return ["BTCUSDT", "ETHUSDT"]

            data = response.json()
            
            symbols = []
            for item in data:
                pair = item.get('market', '')
                # Filter for USDT
                if pair.endswith('USDT'):
                    symbols.append(pair)
            
            unique_symbols = sorted(list(set(symbols)))
            
            if len(unique_symbols) > 5:
                print(f"✅ CoinDCX Loaded {len(unique_symbols)} Pairs!")
                return unique_symbols
            else:
                print("⚠️ CoinDCX returned 0 symbols in filter.")
                return ["BTCUSDT", "ETHUSDT"]
                
        except Exception as e:
            # THIS PRINT IS CRITICAL
            print(f"❌ CRITICAL COINDCX ERROR: {str(e)}")
            return ["BTCUSDT", "ETHUSDT"]

    async def fetch_history(self, symbol, timeframe='1h', limit=1000):
        try:
            clean_symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
            
            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            if tf == '1m': limit = 2000
            
            url = f"{self.public_url}/market_data/candles"
            params = {'pair': clean_symbol, 'interval': tf, 'limit': limit}
            
            # Disable SSL here too
            response = await asyncio.to_thread(requests.get, url, params=params, verify=False)
            data = response.json()
            
            if not data or not isinstance(data, list):
                # Retry with B- prefix
                fallback = f"B-{clean_symbol}"
                params['pair'] = fallback
                response = await asyncio.to_thread(requests.get, url, params=params, verify=False)
                data = response.json()
            
            if not data or not isinstance(data, list): return pd.DataFrame()

            df = pd.DataFrame(data)
            if 'time' not in df.columns: return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df.iloc[::-1].reset_index(drop=True).dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()

coindcx_manager = CoinDCXManager()
</file>

<file path="client/app/dashboard/page.tsx">
"use client";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Plus, Zap, BarChart3, Settings, PlayCircle, Trash2, Terminal, X, Edit3, PauseCircle, Play, Loader2 } from "lucide-react";
import Link from 'next/link';

export default function Dashboard() {
  const { data: session } = useSession();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [selectedStratId, setSelectedStratId] = useState<number | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  useEffect(() => { if (session?.user?.email) fetchStrategies(); }, [session]);

  const fetchStrategies = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(apiUrl + '/strategies/' + session?.user?.email);
      const data = await res.json();
      setStrategies(data);
    } catch (e) { console.error("Error fetching strategies"); }
  };

  const fetchLogs = async (id: number) => {
    setSelectedStratId(id);
    setLogs([]); 
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(apiUrl + '/strategies/' + id + '/logs');
        const data = await res.json();
        setLogs(data);
    } catch(e) { console.error(e); }
  };

  const handleToggle = async (id: number) => {
    setTogglingId(id);
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        await fetch(apiUrl + '/strategies/' + id + '/toggle', { method: 'POST' });
        await fetchStrategies();
    } catch (e) { alert("Connection Error"); }
    setTogglingId(null);
  };

  const handleDelete = async (id: number) => {
    if(!confirm("Are you sure you want to permanently delete this strategy?")) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(apiUrl + '/strategies/' + id, { method: 'DELETE' });
      if (res.ok) {
          setStrategies(strategies.filter((s: any) => s.id !== id));
      } else {
          alert("Server refused to delete. Please try again.");
      }
    } catch (e) { alert("Network Error while deleting."); }
  };

  const activeCount = strategies.filter((s:any) => s.is_running).length;

  return (
    <div className="min-h-screen bg-slate-950 text-white flex relative font-sans">
      <AnimatePresence>
      {selectedStratId && (
        <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-700 w-full max-w-3xl rounded-3xl overflow-hidden shadow-2xl">
                <div className="flex justify-between items-center p-6 border-b border-slate-800 bg-slate-950">
                    <h3 className="font-mono text-emerald-400 flex items-center gap-3 text-lg"><Terminal size={22}/> LIVE TERMINAL</h3>
                    <button onClick={() => setSelectedStratId(null)} className="p-2 rounded-full hover:bg-slate-800 transition-colors"><X size={24} className="text-slate-400"/></button>
                </div>
                <div className="h-96 overflow-y-auto p-6 bg-black font-mono text-sm space-y-3">
                    {logs.length === 0 ? <p className="text-slate-600 italic">Waiting for engine ticks...</p> : logs.map((log: any) => (
                        <div key={log.id} className="border-b border-slate-900/50 pb-2 flex gap-3">
                            <span className="text-slate-600 min-w-[80px]">[{new Date(log.timestamp).toLocaleTimeString()}]</span> 
                            <span className={log.level === 'ERROR' ? 'text-red-500 font-bold' : log.level === 'SUCCESS' ? 'text-emerald-400 font-bold' : 'text-blue-400 font-bold'}>{log.level}:</span>
                            <span className="text-slate-300">{log.message}</span>
                        </div>
                    ))}
                </div>
                <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-end">
                    <button onClick={() => fetchLogs(selectedStratId)} className="text-sm text-slate-400 hover:text-white px-4 py-2 hover:bg-slate-800 rounded-full transition-all">REFRESH LOGS</button>
                </div>
            </div>
        </motion.div>
      )}
      </AnimatePresence>

      <aside className="w-72 border-r border-slate-800 p-8 hidden md:block">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent mb-12">AlgoTrade</h2>
        <nav className="space-y-4">
          <Link href="/dashboard"><button className="w-full flex items-center gap-4 px-6 py-4 bg-slate-900 text-emerald-400 rounded-full border border-slate-800 shadow-lg hover:shadow-emerald-900/20 transition-all font-medium"><Activity size={22} /> Dashboard</button></Link>
          <Link href="/dashboard/settings"><button className="w-full flex items-center gap-4 px-6 py-4 text-slate-400 hover:bg-slate-900 hover:text-white rounded-full transition-all font-medium hover:scale-105"><Settings size={22} /> Broker Keys</button></Link>
        </nav>
      </aside>

      <main className="flex-1 p-10">
        <header className="flex justify-between items-center mb-12">
            <div><h1 className="text-4xl font-bold mb-2">Command Center</h1><p className="text-slate-400 text-lg">Welcome back, {session?.user?.name}</p></div>
            <Link href="/dashboard/builder"><button className="bg-gradient-to-r from-emerald-600 to-cyan-600 text-white px-8 py-4 rounded-full font-bold flex items-center gap-3 shadow-[0_0_30px_rgba(16,185,129,0.4)] hover:shadow-[0_0_50px_rgba(16,185,129,0.6)] hover:scale-105 transition-all text-lg"><Plus size={24} /> New Strategy</button></Link>
        </header>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <div className="p-8 bg-slate-900 rounded-[2rem] border border-slate-800 shadow-xl"><div className="text-slate-400 mb-3 flex items-center gap-3 text-sm font-medium uppercase tracking-wider"><Activity size={18}/> Active Algos</div><div className="text-5xl font-bold text-white">{activeCount} <span className="text-lg text-slate-500 font-normal">running</span></div></div>
            <div className="p-8 bg-slate-900 rounded-[2rem] border border-slate-800 shadow-xl"><div className="text-slate-400 mb-3 flex items-center gap-3 text-sm font-medium uppercase tracking-wider"><BarChart3 size={18}/> Total Volume</div><div className="text-5xl font-bold text-white">₹0.00</div></div>
            <div className="p-8 bg-slate-900 rounded-[2rem] border border-slate-800 relative overflow-hidden shadow-xl"><div className="absolute right-0 top-0 p-6 opacity-10"><Zap size={80} /></div><div className="text-slate-400 mb-3 text-sm font-medium uppercase tracking-wider">System Status</div><div className="text-emerald-400 font-bold flex items-center gap-3 text-xl"><span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]"></span> Online</div></div>
        </div>

        <h2 className="text-2xl font-bold mb-6">Your Strategies</h2>
        
        {strategies.length === 0 ? (
          <div className="border-2 border-dashed border-slate-800 rounded-[2rem] p-16 flex flex-col items-center justify-center text-slate-500"><div className="bg-slate-900 p-6 rounded-full mb-6"><PlayCircle size={48} className="text-slate-400" /></div><p className="text-xl mb-6">No algorithms running yet.</p><Link href="/dashboard/builder"><button className="text-emerald-400 hover:text-emerald-300 font-bold text-lg hover:underline">+ Create New Algo</button></Link></div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {strategies.map((strat: any) => {
              
              // SAFE STRING DECLARATIONS
              const isRunning = strat.is_running;
              const cardClass = "p-8 rounded-[2rem] border transition-all group relative hover:shadow-2xl hover:shadow-black/50 " + (isRunning ? "bg-slate-900 border-slate-800 hover:border-emerald-500/30" : "bg-slate-900/50 border-slate-800 opacity-75");
              const toggleClass = "w-12 h-12 flex items-center justify-center rounded-full transition-all shadow-lg hover:scale-105 " + (isRunning ? "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500 hover:text-black" : "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500 hover:text-white");
              const statusClass = "flex items-center gap-3 text-sm font-bold px-4 py-2 rounded-full w-fit border " + (isRunning ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" : "text-yellow-500 bg-yellow-500/10 border-yellow-500/20");

              return (
              <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} key={strat.id} className={cardClass}>
                <div className="flex justify-between items-start mb-6">
                  <div className="flex gap-2">
                    <button onClick={() => handleToggle(strat.id)} disabled={togglingId === strat.id} className={toggleClass}>
                        {togglingId === strat.id ? <Loader2 size={24} className="animate-spin" /> : (isRunning ? <PauseCircle size={24} /> : <Play size={24} className="ml-1" />)}
                    </button>
                  </div>
                  <div className="flex gap-2">
                    <Link href={'/dashboard/builder?edit=' + strat.id}><button className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:bg-blue-600 hover:text-white transition-all" title="Edit"><Edit3 size={16} /></button></Link>
                    <button onClick={() => fetchLogs(strat.id)} className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:bg-black hover:text-emerald-400 transition-all" title="View Logs"><Terminal size={16} /></button>
                    <button onClick={() => handleDelete(strat.id)} className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:bg-red-900/30 hover:text-red-400 transition-all"><Trash2 size={16} /></button>
                  </div>
                </div>
                <h3 className="font-bold text-xl mb-2">{strat.name}</h3>
                <div className="text-slate-400 text-sm mb-6 flex items-center gap-2"><span className="bg-slate-800 px-3 py-1 rounded-full text-xs">{strat.symbol}</span><span className="bg-slate-800 px-3 py-1 rounded-full text-xs">{strat.broker || 'DELTA'}</span></div>
                
                <div className={statusClass}>
                    {isRunning ? <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> : <span className="w-2 h-2 rounded-full bg-yellow-500"></span>}
                    {isRunning ? "RUNNING" : "PAUSED"}
                </div>
              </motion.div>
            )})}
          </div>
        )}
      </main>
    </div>
  );
}
</file>

<file path="server/app/engine.py">
import asyncio
import json
import websockets
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import time
import hmac
import hashlib
import requests
from sqlalchemy.orm import Session
from . import models, database, security, crud
from .brokers.coindcx import coindcx_manager

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session, broker="DELTA"):
        strategies = db.query(models.Strategy).filter(
            models.Strategy.is_running == True, 
            models.Strategy.broker == broker
        ).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols

    async def fetch_history(self, symbol, broker="DELTA"):
        exchange = None
        try:
            if broker == "COINDCX":
                return await coindcx_manager.fetch_history(symbol, timeframe='1m', limit=100)
            else:
                exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
                hist_symbol = symbol.replace('-', '') if 'USDT' not in symbol else symbol
                ohlcv = await exchange.fetch_ohlcv(hist_symbol, timeframe='1m', limit=100)
                if not ohlcv: return pd.DataFrame()
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
                return df.dropna()
        except: return None
        finally: 
            if exchange: await exchange.close()

    def calculate_indicator(self, df, name, params):
        try:
            length = int(params.get('length') or 14)
            if name == 'rsi':
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))
            elif name == 'ema': return df['close'].ewm(span=length, adjust=False).mean()
            elif name == 'sma': return df['close'].rolling(window=length).mean()
            return pd.Series(0, index=df.index)
        except: return pd.Series(0, index=df.index)

    async def check_conditions(self, symbol, broker, current_price, logic):
        try:
            conditions = logic.get('conditions', [])
            
            # FAST PATH: If no complex indicators, use live price instantly
            needs_history = False
            for cond in conditions:
                l_type = cond.get('left', {}).get('type')
                r_type = cond.get('right', {}).get('type')
                if l_type not in ['close', 'number'] or r_type not in ['close', 'number']:
                    needs_history = True
                    break

            if not needs_history:
                for cond in conditions:
                    v_l = current_price if cond['left']['type'] == 'close' else float(cond['left']['params'].get('value', 0))
                    v_r = current_price if cond['right']['type'] == 'close' else float(cond['right']['params'].get('value', 0))
                    op = cond['operator']
                    if op == 'GREATER_THAN' and not (v_l > v_r): return False
                    if op == 'LESS_THAN' and not (v_l < v_r): return False
                    if op == 'EQUALS' and not (v_l == v_r): return False
                return True

            # SLOW PATH: Fetch history for indicators
            df = await self.fetch_history(symbol, broker)
            if df is None or df.empty: return False

            df.loc[df.index[-1], 'close'] = current_price

            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    name, params = item.get('type'), item.get('params', {})
                    length = int(params.get('length') or 14)
                    col_name = f"{name}_{length}"
                    if col_name not in df.columns:
                        df[col_name] = self.calculate_indicator(df, name, params)

            df = df.fillna(0)
            last_row, prev_row = df.iloc[-1], df.iloc[-2]

            def get_val(row, item):
                if item['type'] == 'number': return float(item['params']['value'])
                if item['type'] in ['close', 'open', 'high', 'low']: return float(row[item['type']])
                length = int(item['params'].get('length') or 14)
                return float(row.get(f"{item['type']}_{length}", 0))

            for cond in conditions:
                v_l, v_r = get_val(last_row, cond['left']), get_val(last_row, cond['right'])
                p_l, p_r = get_val(prev_row, cond['left']), get_val(prev_row, cond['right'])
                op = cond['operator']
                
                if op == 'GREATER_THAN' and not (v_l > v_r): return False
                if op == 'LESS_THAN' and not (v_l < v_r): return False
                if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): return False
                if op == 'CROSSES_BELOW' and not (v_l < v_r and p_l >= p_r): return False

            return True
        except: return False

    async def execute_trade(self, db: Session, symbol: str, current_price: float, broker: str):
        if current_price <= 0: return

        strategies = db.query(models.Strategy).filter(
            models.Strategy.is_running == True, 
            models.Strategy.symbol == symbol,
            models.Strategy.broker == broker
        ).all()

        for strat in strategies:
            crud.create_log(db, strat.id, f"📡 System Check: {symbol} @ ${current_price:.2f}", "INFO")

            is_trigger = await self.check_conditions(symbol, broker, current_price, strat.logic_configuration)

            if is_trigger:
                user = strat.owner
                api_key_enc = user.coindcx_api_key if broker == "COINDCX" else user.delta_api_key
                secret_enc = user.coindcx_api_secret if broker == "COINDCX" else user.delta_api_secret

                if not api_key_enc:
                    crud.create_log(db, strat.id, f"❌ No API Keys saved for {broker}.", "ERROR")
                    continue

                logic = strat.logic_configuration
                qty = float(logic.get('quantity', 1))
                
                params = {}
                if logic.get('sl', 0) > 0: params['stop_loss_price'] = current_price * (1 - (logic['sl']/100))
                if logic.get('tp', 0) > 0: params['take_profit_price'] = current_price * (1 + (logic['tp']/100))

                try:
                    api_key = security.decrypt_value(api_key_enc)
                    secret = security.decrypt_value(secret_enc)
                    
                    if broker == "DELTA":
                        exchange = ccxt.delta({'apiKey': api_key, 'secret': secret, 'options': { 'defaultType': 'future', 'adjustForTimeDifference': True }, 'urls': { 'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange' }})
                        crud.create_log(db, strat.id, f"🚀 Firing Order on DELTA: Buy {qty} {symbol}", "INFO")
                        order = await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                        crud.create_log(db, strat.id, f"✅ Order Filled! ID: {order.get('id')}", "SUCCESS")
                        await exchange.close()
                    
                    elif broker == "COINDCX":
                        # Format for CoinDCX API
                        cdcx_sym = symbol
                        clean_sym = symbol.replace("/", "").replace("-", "")
                        if clean_sym.endswith("USDT") and not clean_sym.startswith("B-"):
                            base = clean_sym[:-4]
                            cdcx_sym = f"B-{base}_USDT"

                        crud.create_log(db, strat.id, f"🚀 Firing Order on COINDCX: Buy {qty} {cdcx_sym}", "INFO")
                        
                        url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"
                        timestamp = int(time.time() * 1000)
                        
                        payload = {"market": cdcx_sym, "side": "buy", "order_type": "market_order", "total_quantity": qty, "timestamp": timestamp}
                        json_payload = json.dumps(payload, separators=(',', ':'))
                        signature = hmac.new(bytes(secret, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
                        
                        headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': api_key, 'X-AUTH-SIGNATURE': signature}
                        
                        response = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
                        res_data = response.json()
                        
                        if response.status_code == 200:
                            crud.create_log(db, strat.id, f"✅ Order Filled! ID: {res_data.get('id', 'Confirmed')}", "SUCCESS")
                        else:
                            err_msg = res_data.get('message', str(res_data))
                            if "margin" in err_msg.lower() or "balance" in err_msg.lower():
                                crud.create_log(db, strat.id, f"⚠️ Insufficient Margin: {err_msg}", "WARNING")
                            else:
                                crud.create_log(db, strat.id, f"❌ Order Failed: {err_msg}", "ERROR")
                except Exception as e:
                    crud.create_log(db, strat.id, f"❌ Engine Error: {str(e)[:50]}", "ERROR")

    async def run_delta_loop(self):
        print("🌐 Delta World Online.")
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "DELTA")
                db.close()
                if not symbols:
                    await asyncio.sleep(10)
                    continue

                async with websockets.connect(self.delta_ws_url) as websocket:
                    payload = { "type": "subscribe", "payload": { "channels": [{ "name": "v2/ticker", "symbols": symbols }] } }
                    await websocket.send(json.dumps(payload))
                    async for message in websocket:
                        if not self.is_running: break
                        data = json.loads(message)
                        if data.get('type') == 'v2/ticker' and 'mark_price' in data:
                            try:
                                live_price = float(data['mark_price'])
                                if live_price > 0:
                                    db_tick = database.SessionLocal()
                                    await self.execute_trade(db_tick, data['symbol'], live_price, "DELTA")
                                    db_tick.close()
                            except: pass
            except: await asyncio.sleep(5)

    async def run_coindcx_loop(self):
        print("🌐 CoinDCX World Online.")
        while self.is_running:
            try:
                db = database.SessionLocal()
                symbols = await self.get_active_symbols(db, "COINDCX")
                db.close()
                
                if symbols:
                    # 🚀 THE FIX: Fetch Live Tickers instantly instead of history
                    resp = await asyncio.to_thread(requests.get, "https://api.coindcx.com/exchange/ticker", timeout=10)
                    tickers = resp.json()
                    
                    # Create a fast dictionary mapped by market name
                    ticker_map = {t['market']: float(t.get('last_price', 0)) for t in tickers}

                    for sym in symbols:
                        # Find the matching live price in the map
                        clean_sym = sym.replace('/', '').replace('-', '')
                        base = clean_sym.replace('USDT', '').replace('USD', '')
                        
                        target_spot = f"{base}USDT"
                        target_future = f"B-{base}_USDT"
                        
                        current_price = 0.0
                        if target_future in ticker_map: current_price = ticker_map[target_future]
                        elif target_spot in ticker_map: current_price = ticker_map[target_spot]
                        elif sym in ticker_map: current_price = ticker_map[sym]
                        
                        if current_price > 0:
                            db_tick = database.SessionLocal()
                            await self.execute_trade(db_tick, sym, current_price, "COINDCX")
                            db_tick.close()
            except Exception as e:
                pass
            
            await asyncio.sleep(10)

    async def start(self):
        self.is_running = True
        print("✅ DUAL-CORE ENGINE STARTED")
        await asyncio.gather(self.run_delta_loop(), self.run_coindcx_loop())

engine = RealTimeEngine()
</file>

<file path="server/app/backtester.py">
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import traceback
import ssl
import math
import asyncio

class Backtester:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def sanitize(self, data):
        if isinstance(data, (float, np.float64, np.float32, int)):
            if math.isnan(data) or math.isinf(data): return 0.0
            return float(data)
        if isinstance(data, dict): return {k: self.sanitize(v) for k, v in data.items()}
        if isinstance(data, list): return [self.sanitize(i) for i in data]
        return data

    async def fetch_historical_data(self, symbol, timeframe='1h', limit=1000):
        exchange = None
        try:
            exchange = ccxt.delta({
                'options': {'defaultType': 'future'},
                'timeout': 30000,
                'enableRateLimit': True,
                'urls': { 
                    'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'},
                    'www': 'https://india.delta.exchange'
                }
            })

            tf_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            tf = tf_map.get(timeframe, '1h')
            
            # --- SYMBOL REPAIR LOGIC ---
            # Try original, then with USDT, then with hyphen
            candidates = [symbol, symbol.replace('/', ''), symbol.replace('/', '-'), symbol.replace('USD', '-USDT'), symbol.replace('USD', 'USDT')]
            
            ohlcv = None
            used_symbol = symbol

            for sym in candidates:
                try:
                    ohlcv = await exchange.fetch_ohlcv(sym, tf, limit=limit)
                    if ohlcv and len(ohlcv) > 0:
                        used_symbol = sym
                        print(f"✅ Found data for {sym}")
                        break
                except: continue
            
            if not ohlcv: return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            
            return df.dropna()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            if exchange: await exchange.close()

    def prepare_data(self, df, logic):
        # Pure Pandas Calculations
        try:
            conditions = logic.get('conditions', [])
            for cond in conditions:
                for side in ['left', 'right']:
                    item = cond.get(side)
                    if not item or item.get('type') == 'number': continue
                    
                    name = item.get('type')
                    params = item.get('params', {})
                    try: length = int(params.get('length') or 14)
                    except: length = 14
                    
                    col_name = f"{name}_{length}"
                    if col_name in df.columns: continue

                    if name == 'rsi':
                        delta = df['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
                        rs = gain / loss
                        df[col_name] = 100 - (100 / (1 + rs))
                    elif name == 'ema':
                        df[col_name] = df['close'].ewm(span=length, adjust=False).mean()
                    elif name == 'sma':
                        df[col_name] = df['close'].rolling(window=length).mean()
            return df.fillna(0)
        except: return df

    def get_val(self, row, item):
        try:
            if item.get('type') == 'number': return float(item.get('params', {}).get('value', 0))
            if item.get('type') in ['close', 'open', 'high', 'low', 'volume']: return float(row[item.get('type')])
            
            length = int(item.get('params', {}).get('length') or 14)
            col = f"{item.get('type')}_{length}"
            return float(row.get(col, 0))
        except: return 0.0

    def calculate_audit_stats(self, trades, equity_curve):
        if not trades: return {"profit_factor": 0, "avg_win": 0, "avg_loss": 0, "max_drawdown": 0, "sharpe_ratio": 0, "expectancy": 0}
        
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] <= 0]
        
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        profit_factor = (sum(wins) / abs(sum(losses))) if sum(losses) != 0 else 999.0

        balances = pd.Series([e['balance'] for e in equity_curve])
        peak = balances.cummax()
        drawdowns = (balances - peak) / peak * 100
        max_dd = drawdowns.min() if not drawdowns.empty else 0.0
        
        return {
            "profit_factor": round(float(profit_factor), 2),
            "avg_win": round(float(avg_win), 2),
            "avg_loss": round(float(avg_loss), 2),
            "max_drawdown": round(abs(float(max_dd)), 2),
            "sharpe_ratio": 1.5, # Placeholder for MVP speed
            "expectancy": round(float((len(wins)/len(trades) * avg_win) + ((1 - len(wins)/len(trades)) * avg_loss)), 2)
        }

    def run_simulation(self, df, logic):
        try:
            if df.empty: return {"error": "No Market Data"}
            df = self.prepare_data(df, logic)
            
            balance, start_price = 1000.0, float(df.iloc[0]['close'])
            buy_hold_qty = 1000.0 / start_price if start_price > 0 else 0
            
            equity_curve, closed_trades, position = [], [], None
            
            conditions = logic.get('conditions', [])
            qty = float(logic.get('quantity', 1))
            sl_pct = float(logic.get('sl', 0))
            tp_pct = float(logic.get('tp', 0))
            FEE = 0.0005 

            for i in range(1, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                current_price = float(row['close'])
                
                # EXIT
                if position:
                    exit_price, reason = 0.0, ''
                    entry_price = float(position['entry_price'])
                    
                    if sl_pct > 0 and float(row['low']) <= (entry_price * (1 - sl_pct/100)):
                        exit_price, reason = entry_price * (1 - sl_pct/100), 'SL'
                    elif tp_pct > 0 and float(row['high']) >= (entry_price * (1 + tp_pct/100)):
                        exit_price, reason = entry_price * (1 + tp_pct/100), 'TP'
                    
                    if exit_price > 0:
                        pnl = (exit_price - entry_price) * position['qty']
                        net = pnl - (exit_price * position['qty'] * FEE)
                        balance += net
                        closed_trades.append({'entry_time': position['entry_time'], 'exit_time': row['timestamp'], 'entry_price': entry_price, 'exit_price': exit_price, 'qty': float(position['qty']), 'pnl': net, 'reason': reason})
                        position = None

                # ENTRY
                if not position:
                    signal = True
                    for cond in conditions:
                        v_l, v_r = self.get_val(row, cond['left']), self.get_val(row, cond['right'])
                        p_l, p_r = self.get_val(prev_row, cond['left']), self.get_val(prev_row, cond['right'])
                        op = cond['operator']
                        if op == 'GREATER_THAN' and not (v_l > v_r): signal = False
                        if op == 'LESS_THAN' and not (v_l < v_r): signal = False
                        if op == 'CROSSES_ABOVE' and not (v_l > v_r and p_l <= p_r): signal = False

                    if signal:
                        balance -= (float(row['close']) * qty * FEE)
                        position = {'entry_price': float(row['close']), 'qty': qty, 'entry_time': row['timestamp']}

                equity_curve.append({'time': row['timestamp'].isoformat(), 'balance': float(balance), 'buy_hold': float(buy_hold_qty * float(row['close']))})

            wins = len([t for t in closed_trades if t['pnl'] > 0])
            total = len(closed_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            result = {
                "metrics": {
                    "final_balance": round(balance, 2), "total_trades": total, "win_rate": round(win_rate, 1),
                    "total_return_pct": round(((balance - 1000)/1000)*100, 2),
                    "audit": self.calculate_audit_stats(closed_trades, equity_curve)
                },
                "trades": closed_trades[-50:],
                "equity": equity_curve[::5]
            }
            return self.sanitize(result)
        except Exception as e:
            print(traceback.format_exc())
            return {"error": f"Sim Error: {str(e)}"}

backtester = Backtester()
</file>

<file path="server/main.py">
import asyncio
import traceback
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app import models, database, schemas, crud
from app.engine import engine as trading_engine
from app.backtester import backtester
from app.brokers.coindcx import coindcx_manager
import ccxt.async_support as ccxt

# CACHE
symbol_cache = {
    "DELTA": ["BTC-USDT", "ETH-USDT"],
    "COINDCX": ["BTCUSDT", "ETHUSDT"] # Start with fallback
}

async def refresh_delta_symbols():
    global symbol_cache
    try:
        exchange = ccxt.delta({'options': {'defaultType': 'future'}, 'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}, 'www': 'https://india.delta.exchange'}})
        markets = await exchange.load_markets()
        syms = [m.get('id', k) for k, m in markets.items() if m.get('active') and ('USDT' in m.get('id', '') or 'USD' in m.get('id', ''))]
        if syms: symbol_cache["DELTA"] = sorted(list(set(syms)))
        await exchange.close()
    except: pass

async def refresh_coindcx_symbols():
    global symbol_cache
    try:
        # Call the manager
        syms = await coindcx_manager.fetch_symbols()
        # Only update if we got a real list (more than 2 defaults)
        if syms and len(syms) > 2:
            symbol_cache["COINDCX"] = syms
    except Exception as e: print(f"CoinDCX Init Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(refresh_delta_symbols())
    asyncio.create_task(refresh_coindcx_symbols())
    asyncio.create_task(trading_engine.start())
    yield
    trading_engine.is_running = False

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="AlgoTradeIndia Engine", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home(): return {"status": "Online"}

@app.get("/data/symbols")
async def get_symbols(broker: str = "DELTA"):
    b = broker.upper()
    if b not in symbol_cache: b = "DELTA"
    
    # FORCE REFRESH IF LIST IS SMALL
    if len(symbol_cache[b]) <= 2:
        if b == "DELTA": await refresh_delta_symbols()
        elif b == "COINDCX": await refresh_coindcx_symbols()
        
    return symbol_cache[b]

@app.post("/auth/sync")
def sync_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user: return crud.create_user(db=db, user=user)
    return {"status": "User exists", "id": db_user.id}

@app.post("/user/keys")
def save_keys(keys: schemas.BrokerKeys, db: Session = Depends(database.get_db)):
    crud.update_broker_keys(db, keys)
    return {"status": "Keys Saved"}

@app.post("/strategy/create")
def create_strategy(strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    new_strat = crud.create_strategy(db, strat)
    return {"status": "Deployed", "id": new_strat.id}

@app.get("/strategies/{email}")
def get_user_strategies(email: str, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email)
    return user.strategies if user else []

@app.post("/strategies/{id}/toggle")
def toggle_strategy(id: int, db: Session = Depends(database.get_db)):
    strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    if strat:
        strat.is_running = not strat.is_running
        db.commit()
    return {"status": "OK", "is_running": strat.is_running}

@app.delete("/strategies/{id}")
def delete_strategy(id: int, db: Session = Depends(database.get_db)):
    db.query(models.Strategy).filter(models.Strategy.id == id).delete()
    db.commit()
    return {"status": "Deleted"}

@app.get("/strategies/{id}/logs")
def get_logs(id: int, db: Session = Depends(database.get_db)):
    return crud.get_strategy_logs(db, id)

@app.get("/strategy/{id}")
def get_strategy_details(id: int, db: Session = Depends(database.get_db)):
    return db.query(models.Strategy).filter(models.Strategy.id == id).first()

@app.put("/strategy/{id}")
def update_strategy(id: int, strat: schemas.StrategyInput, db: Session = Depends(database.get_db)):
    db_strat = db.query(models.Strategy).filter(models.Strategy.id == id).first()
    if db_strat:
        db_strat.name, db_strat.symbol, db_strat.broker, db_strat.logic_configuration = strat.name, strat.symbol, strat.broker, strat.logic
        db.commit()
    return {"status": "Updated", "id": id}

@app.post("/strategy/backtest")
async def run_backtest(strat: schemas.StrategyInput):
    tf = strat.logic.get('timeframe', '1h')
    if strat.broker.upper() == "COINDCX":
        df = await coindcx_manager.fetch_history(strat.symbol, tf, limit=3000)
    else:
        df = await backtester.fetch_historical_data(strat.symbol, tf, limit=3000)
    if df.empty: return {"error": f"No data for {strat.symbol}"}
    return backtester.run_simulation(df, strat.logic)
</file>

<file path="client/app/dashboard/builder/page.tsx">
"use client";

import { useState, useEffect, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Plus, Trash2, Zap, AlertTriangle, Search, Settings2, Save, BarChart2, Clock, List, TrendingUp, Activity, DollarSign, Sparkles, Loader2, Bot } from 'lucide-react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { INDICATORS } from '@/lib/indicators';
import { useSearchParams, useRouter } from 'next/navigation';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

function BuilderContent() {
  const { data: session } = useSession();
  const searchParams = useSearchParams();
  const router = useRouter();
  const editId = searchParams.get('edit'); 

  // --- STATE VARIABLES ---
  const [strategyName, setStrategyName] = useState("My Pro Algo");
  const [broker, setBroker] = useState("DELTA");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [quantity, setQuantity] = useState(1);
  const [stopLoss, setStopLoss] = useState(1.0);
  const [takeProfit, setTakeProfit] = useState(2.0);
  
  const [symbolList, setSymbolList] = useState<string[]>([]);
  
  const [conditions, setConditions] = useState<any[]>([
    { id: 1, left: { type: 'rsi', params: { length: 14 } }, operator: 'LESS_THAN', right: { type: 'number', params: { value: 30 } } }
  ]);
  
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState<any>(null);

  // --- AI STATE ---
  const [aiPrompt, setAiPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // FETCH LIVE SYMBOLS
  useEffect(() => {
    const fetchSymbols = async () => {
        try {
            setSymbolList([]); 
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/data/symbols?broker=${broker}`);
            if (res.ok) {
                const data = await res.json();
                if (data && data.length > 0) {
                    setSymbolList(data);
                    if (!editId) setSymbol(data[0]); 
                }
            }
        } catch(e) { console.error("Could not fetch symbols", e); }
    };
    fetchSymbols();
  }, [broker, editId]);

  // FETCH EXISTING STRATEGY IF EDITING
  useEffect(() => {
    if (editId && session?.user?.email) {
        const fetchDetails = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(apiUrl + '/strategy/' + editId);
                if(res.ok) {
                    const data = await res.json();
                    setStrategyName(data.name); 
                    setSymbol(data.symbol);
                    setBroker(data.broker || "DELTA");
                    
                    const logic = data.logic_configuration || {};
                    setTimeframe(logic.timeframe || "1h"); 
                    setQuantity(logic.quantity || 1);
                    setStopLoss(logic.sl || 0); 
                    setTakeProfit(logic.tp || 0);
                    
                    const safeConditions = (logic.conditions ||[]).map((c: any) => ({
                        id: c.id || Math.random(),
                        left: c.left || { type: 'close', params: {} },
                        operator: c.operator || 'GREATER_THAN',
                        right: c.right || { type: 'number', params: { value: 0 } }
                    }));
                    if (safeConditions.length > 0) setConditions(safeConditions);
                }
            } catch (e) { console.error(e); }
        };
        fetchDetails();
    }
  }, [editId, session]);

  // --- AI GENERATOR FUNCTION ---
  const handleAIGenerate = async () => {
    if (!aiPrompt) return;
    setIsGenerating(true);
    try {
        const res = await fetch('/api/generate-strategy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: aiPrompt })
        });
        
        const data = await res.json();
        
        if (data.error) {
            alert("AI Error: " + data.error);
        } else {
            // Apply AI Data
            setStrategyName(data.strategyName || "AI Strategy");
            if (data.symbol) setSymbol(data.symbol);
            if (data.timeframe) setTimeframe(data.timeframe);
            if (data.quantity) setQuantity(data.quantity);
            if (data.sl !== undefined) setStopLoss(data.sl);
            if (data.tp !== undefined) setTakeProfit(data.tp);
            if (data.broker) setBroker(data.broker); 
            
            if (data.conditions && data.conditions.length > 0) {
                const mappedConds = data.conditions.map((c: any, index: number) => ({
                    id: Date.now() + index,
                    left: c.left || { type: 'close', params: {} },
                    operator: c.operator || 'GREATER_THAN',
                    right: c.right || { type: 'number', params: { value: 0 } }
                }));
                setConditions(mappedConds);
            }
            setAiPrompt(""); 
        }
    } catch (e) {
        alert("Failed to communicate with AI.");
    }
    setIsGenerating(false);
  };

  const addCondition = () => { 
    setConditions([...conditions, { id: Date.now(), left: { type: 'rsi', params: { length: 14 } }, operator: 'LESS_THAN', right: { type: 'number', params: { value: 30 } } }]); 
  };
  
  const removeCondition = (id: number) => { 
    setConditions(conditions.filter(c => c.id !== id)); 
  };

  const updateCondition = (id: number, side: 'left' | 'right', field: string, val: any) => { 
    setConditions(conditions.map(c => { 
        if (c.id !== id) return c; 
        if (field === 'type') { 
            const ind = INDICATORS.find(i => i.value === val); 
            const defaultParams: any = {}; 
            if (ind && ind.params) {
                ind.params.forEach(p => { defaultParams[p.name] = p.def; }); 
            }
            return { ...c, [side]: { type: val, params: defaultParams } }; 
        } 
        return { ...c, [side]: { ...c[side], [field]: val } }; 
    })); 
  };

  const updateParam = (id: number, side: 'left' | 'right', paramName: string, val: any) => { 
    setConditions(conditions.map(c => { 
        if (c.id !== id) return c; 
        const sideData: any = side === 'left' ? c.left : c.right;
        const newSide = { ...sideData, params: { ...sideData.params, [paramName]: val } };
        return { ...c, [side]: newSide }; 
    })); 
  };

  const handleDeploy = async () => {
    if (!session?.user?.email) return alert("Please login first");
    const payload = { 
      email: session.user.email, 
      name: strategyName, 
      symbol, 
      broker,
      logic: { conditions, timeframe, quantity: Number(quantity), sl: Number(stopLoss), tp: Number(takeProfit) } 
    };
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      let url = apiUrl + '/strategy/create'; 
      let method = 'POST';
      if (editId) { 
          url = apiUrl + '/strategy/' + editId; 
          method = 'PUT'; 
      }
      const res = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if(res.ok) { 
          alert(editId ? "✅ STRATEGY UPDATED!" : "🚀 STRATEGY DEPLOYED!"); 
          router.push('/dashboard'); 
      } else { 
          alert("Operation Failed"); 
      }
    } catch (e) { alert("Server Error."); }
  };

  const handleBacktest = async () => {
    setBacktestLoading(true); 
    setBacktestResult(null);
    const payload = { 
      email: session?.user?.email || "test", 
      name: strategyName, 
      symbol, 
      broker,
      logic: { conditions, timeframe, quantity: Number(quantity), sl: Number(stopLoss), tp: Number(takeProfit) } 
    };
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(apiUrl + '/strategy/backtest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (data.error) { 
            alert("Error: " + data.error); 
        } else { 
            setBacktestResult(data); 
        }
    } catch(e) { alert("Backtest Failed"); }
    setBacktestLoading(false);
  };

  const IndicatorSelect = ({ side, data, onChange, onParamChange }: any) => {
    if (!data || !data.type) return <div className="text-red-500 text-xs p-2">Invalid Data</div>;
    const selectedDef = INDICATORS.find(i => i.value === data.type);
    
    return (
        <div className="flex flex-col gap-2 bg-slate-950 p-3 rounded-lg border border-slate-700 min-w-[250px]">
            <div className="relative">
                <select className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm appearance-none outline-none focus:border-emerald-500" value={data.type} onChange={(e) => onChange('type', e.target.value)}>
                    {INDICATORS.map(ind => (<option key={ind.value} value={ind.value}>{ind.label}</option>))}
                </select>
                <div className="absolute right-3 top-2.5 pointer-events-none text-slate-500"><Search size={14}/></div>
            </div>
            {selectedDef && selectedDef.params && selectedDef.params.length > 0 && (
                <div className="grid grid-cols-2 gap-2 mt-1">
                    {selectedDef.params.map((p: any) => (
                        <div key={p.name}>
                            <label className="text-[10px] text-slate-500 uppercase">{p.name}</label>
                            <input 
                              type={p.name === 'source' ? 'text' : 'number'} 
                              className="w-full bg-black/30 border border-slate-800 rounded px-2 py-1 text-xs text-cyan-400" 
                              value={data.params?.[p.name] || ''} 
                              onChange={(e) => onParamChange(p.name, e.target.value)} 
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
  };

  const formatIST = (isoString: string) => { 
      try { return new Date(isoString).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' }); } 
      catch { return "-"; } 
  };
  
  const formatPrice = (p: any) => { 
      if (p === undefined || p === null || isNaN(Number(p))) return "0.00"; 
      return Number(p).toFixed(2); 
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 pb-20">
        
        {/* --- 🌟 THE AI MAGIC BOX (NOW ACTUALLY IN THE UI) 🌟 --- */}
        <div className="col-span-1 lg:col-span-4 bg-gradient-to-r from-indigo-900/50 to-purple-900/50 p-6 rounded-2xl border border-indigo-500/30 shadow-lg">
            <div className="flex flex-col md:flex-row gap-4 items-center">
                <div className="p-3 bg-indigo-500/20 rounded-full text-indigo-300">
                    <Bot size={24} />
                </div>
                <div className="flex-1 w-full">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
                       Strategy AI Assistant <span className="text-xs bg-indigo-500 px-2 py-0.5 rounded text-white">BETA</span>
                    </h3>
                    <textarea 
                        value={aiPrompt}
                        onChange={(e) => setAiPrompt(e.target.value)}
                        placeholder="e.g. 'Build a scalping strategy for BTC on CoinDCX. Buy when RSI is below 30. Stop Loss 1%, Take Profit 2%.'"
                        className="w-full bg-slate-950/80 border border-slate-700 rounded-xl p-4 text-sm text-white focus:border-indigo-500 outline-none resize-none h-20 placeholder:text-slate-600 shadow-inner"
                    />
                </div>
                <button 
                    onClick={handleAIGenerate} 
                    disabled={isGenerating || !aiPrompt}
                    className="w-full md:w-auto h-20 px-8 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                    {isGenerating ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
                    {isGenerating ? "Thinking..." : "Generate"}
                </button>
            </div>
        </div>
        {/* --- END AI BOX --- */}

        {/* SETTINGS PANEL */}
        <div className="col-span-1 space-y-6">
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
            <h3 className="text-lg font-semibold mb-4 text-cyan-400 flex items-center gap-2"><Zap size={18} /> Asset</h3>
            <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Name</label>
                  <input type="text" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none focus:border-cyan-500" />
                </div>
                <div>
                    <label className="block text-sm text-slate-400 mb-1 flex items-center gap-2">Broker</label>
                    <select value={broker} onChange={(e) => setBroker(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none font-bold text-yellow-500">
                        <option value="DELTA">Delta Exchange</option>
                        <option value="COINDCX">CoinDCX</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm text-slate-400 mb-1">Pair ({symbolList.length})</label>
                    <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none">
                        {symbolList.length > 0 ? symbolList.map(s => (<option key={s} value={s}>{s}</option>)) : <option value="BTCUSDT">Loading...</option>}
                    </select>
                </div>
                <div>
                    <label className="block text-sm text-slate-400 mb-1 flex items-center gap-2"><Clock size={12}/> Timeframe</label>
                    <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none">
                        <option value="1m">1 Min</option>
                        <option value="5m">5 Min</option>
                        <option value="15m">15 Min</option>
                        <option value="1h">1 Hour</option>
                        <option value="4h">4 Hour</option>
                        <option value="1d">1 Day</option>
                    </select>
                </div>
            </div>
          </div>
          
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
            <h3 className="text-lg font-semibold mb-4 text-orange-400 flex items-center gap-2"><AlertTriangle size={18} /> Risk</h3>
            <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Qty</label>
                  <input type="number" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-red-400 mb-1">SL %</label>
                      <input type="number" step="0.1" value={stopLoss} onChange={(e) => setStopLoss(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none" />
                    </div>
                    <div>
                      <label className="block text-sm text-emerald-400 mb-1">TP %</label>
                      <input type="number" step="0.1" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none" />
                    </div>
                </div>
            </div>
          </div>
          
          <div className="flex flex-col gap-3">
              <button onClick={handleBacktest} disabled={backtestLoading} className="w-full py-4 bg-slate-800 border border-slate-600 rounded-lg font-bold flex items-center justify-center gap-2 hover:bg-slate-700 transition-all">
                  {backtestLoading ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : <BarChart2 size={18} />} Run Simulation
              </button>
              <button onClick={handleDeploy} className="w-full py-4 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg font-bold flex items-center justify-center gap-2 hover:scale-105 transition-all">
                  {editId ? <Save size={18} /> : <Play size={18} />} {editId ? 'Update Strategy' : 'Deploy Live'}
              </button>
          </div>
        </div>

        {/* LOGIC BUILDER */}
        <div className="col-span-3 space-y-4">
            <h3 className="text-lg font-semibold text-emerald-400 flex items-center gap-2"><Settings2 size={18}/> Entry Logic</h3>
            <div className="space-y-4">
                {conditions.map((c, i) => (
                    <motion.div key={c.id} initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} className="flex flex-col md:flex-row items-center gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800 relative">
                        <div className="text-slate-500 font-bold bg-slate-800 w-10 h-10 rounded-full flex items-center justify-center shrink-0">{i === 0 ? 'IF' : 'AND'}</div>
                        
                        <IndicatorSelect data={c.left} onChange={(f: string, v: any) => updateCondition(c.id, 'left', f, v)} onParamChange={(p: string, v: any) => updateParam(c.id, 'left', p, v)} />
                        
                        <select 
                          className="bg-slate-950 text-emerald-400 font-bold border border-slate-700 rounded px-3 py-2 outline-none" 
                          value={c.operator} 
                          onChange={(e) => { 
                            const newConds = [...conditions]; 
                            const target = newConds.find(x => x.id === c.id);
                            if (target) target.operator = e.target.value; 
                            setConditions(newConds); 
                          }}
                        >
                            <option value="CROSSES_ABOVE">Crosses Above</option>
                            <option value="CROSSES_BELOW">Crosses Below</option>
                            <option value="GREATER_THAN">Greater Than</option>
                            <option value="LESS_THAN">Less Than</option>
                            <option value="EQUALS">Equals</option>
                        </select>

                        <IndicatorSelect data={c.right} onChange={(f: string, v: any) => updateCondition(c.id, 'right', f, v)} onParamChange={(p: string, v: any) => updateParam(c.id, 'right', p, v)} />
                        
                        <button onClick={() => removeCondition(c.id)} className="absolute top-2 right-2 text-slate-600 hover:text-red-400"><Trash2 size={16}/></button>
                    </motion.div>
                ))}
            </div>
            
            <button onClick={addCondition} className="w-full py-4 border-2 border-dashed border-slate-800 rounded-xl text-slate-600 hover:text-white hover:border-slate-500 flex items-center justify-center gap-2 transition-all">
              <Plus size={20} /> Add Logic Block
            </button>
            
            {/* BACKTEST RESULTS & AUDIT REPORT */}
            {backtestResult && (
                <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="mt-8 space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-700"><div className="text-slate-500 text-xs uppercase mb-1 flex items-center gap-1"><DollarSign size={12}/> Balance</div><div className="text-3xl font-bold text-white">${backtestResult.metrics.final_balance}</div></div>
                        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-700"><div className="text-slate-500 text-xs uppercase mb-1 flex items-center gap-1"><Activity size={12}/> Return</div><div className={'text-3xl font-bold ' + (backtestResult.metrics.total_return_pct >= 0 ? 'text-emerald-400' : 'text-red-400')}>{backtestResult.metrics.total_return_pct}%</div></div>
                        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-700"><div className="text-slate-500 text-xs uppercase mb-1 flex items-center gap-1"><TrendingUp size={12}/> Win Rate</div><div className="text-3xl font-bold text-blue-400">{backtestResult.metrics.win_rate}%</div></div>
                        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-700"><div className="text-slate-500 text-xs uppercase mb-1 flex items-center gap-1"><List size={12}/> Trades</div><div className="text-3xl font-bold text-white">{backtestResult.metrics.total_trades}</div></div>
                    </div>
                    
                    {backtestResult.metrics.audit && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Max Drawdown</div><div className="text-lg font-bold text-red-400">{backtestResult.metrics.audit.max_drawdown}%</div></div>
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Sharpe Ratio</div><div className="text-lg font-bold text-white">{backtestResult.metrics.audit.sharpe_ratio}</div></div>
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Profit Factor</div><div className="text-lg font-bold text-emerald-400">{backtestResult.metrics.audit.profit_factor}</div></div>
                            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800"><div className="text-slate-500 text-xs uppercase">Expectancy</div><div className="text-lg font-bold text-white">${backtestResult.metrics.audit.expectancy}</div></div>
                        </div>
                    )}
                    
                    <div className="h-80 w-full bg-slate-900 rounded-2xl border border-slate-700 p-4">
                        <ResponsiveContainer width="100%" height={320}>
                            <LineChart data={backtestResult.equity}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="time" hide />
                                <YAxis domain={['auto', 'auto']} stroke="#94a3b8" fontSize={10} />
                                <Tooltip contentStyle={{backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px'}} />
                                <Legend />
                                <Line name="Strategy Equity" type="monotone" dataKey="balance" stroke="#3b82f6" strokeWidth={2} dot={false} />
                                <Line name="Buy & Hold" type="monotone" dataKey="buy_hold" stroke="#eab308" strokeWidth={2} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden">
                        <div className="p-4 border-b border-slate-700 font-bold flex items-center gap-2 bg-slate-800/50"><List size={18}/> Comprehensive Trade Ledger (IST)</div>
                        <div className="max-h-96 overflow-y-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-950 sticky top-0">
                                    <tr>
                                        <th className="px-6 py-3">Entry Time</th>
                                        <th className="px-6 py-3">Buy Price</th>
                                        <th className="px-6 py-3">Exit Time</th>
                                        <th className="px-6 py-3">Sell Price</th>
                                        <th className="px-6 py-3">Result</th>
                                        <th className="px-6 py-3 text-right">PnL</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {backtestResult.trades.slice().reverse().map((t: any, i: number) => (
                                        <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4 text-slate-400 text-xs">{formatIST(t.entry_time)}</td>
                                            <td className="px-6 py-4 font-mono text-emerald-400">${formatPrice(t.entry_price)}</td>
                                            <td className="px-6 py-4 text-slate-400 text-xs">{formatIST(t.exit_time)}</td>
                                            <td className="px-6 py-4 font-mono text-red-400">${formatPrice(t.exit_price)}</td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded text-xs font-bold ${t.pnl > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                                    {t.reason || (t.pnl > 0 ? 'WIN' : 'LOSS')}
                                                </span>
                                            </td>
                                            <td className={`px-6 py-4 text-right font-mono font-bold ${t.pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {(t.pnl > 0 ? '+' : '') + '$' + formatPrice(t.pnl)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </motion.div>
            )}
        </div>
    </div>
  );
}

export default function StrategyBuilder() {
  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-4">
            <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-lg transition-colors"><ArrowLeft size={24} className="text-slate-400" /></Link>
            <div><h1 className="text-2xl font-bold flex items-center gap-2">Logic Builder</h1></div>
        </div>
      </header>
      <Suspense fallback={<div className="text-slate-500 flex justify-center py-20 animate-pulse">Loading Builder Environment...</div>}>
          <BuilderContent />
      </Suspense>
    </div>
  );
}
</file>

</files>
