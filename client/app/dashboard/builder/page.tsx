"use client";
import { useState, useEffect, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Plus, Trash2, Zap, AlertTriangle, Search, Settings2, Save, BarChart2, Clock, List, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
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

  const [strategyName, setStrategyName] = useState("My Pro Algo");
  const [symbol, setSymbol] = useState("BTCUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [quantity, setQuantity] = useState(1);
  const [stopLoss, setStopLoss] = useState(1.0);
  const [takeProfit, setTakeProfit] = useState(2.0);
  
  // LIVE SYMBOL LIST
  const [symbolList, setSymbolList] = useState(['BTCUSD', 'ETHUSD']); 

  const [conditions, setConditions] = useState([{ id: 1, left: { type: 'rsi', params: { length: 14 } }, operator: 'LESS_THAN', right: { type: 'number', params: { value: 30 } } }]);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState<any>(null);

  // Fetch Symbol List on Load
  useEffect(() => {
    const fetchSymbols = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(apiUrl + '/data/symbols');
            const data = await res.json();
            if (data && data.length > 0) {
                setSymbolList(data);
                setSymbol(data[0]); // Default to first symbol
            }
        } catch(e) { console.error("Could not fetch symbols"); }
    };
    fetchSymbols();
  }, []);

  useEffect(() => {
    if (editId && session?.user?.email) {
        const fetchDetails = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(apiUrl + '/strategy/' + editId);
                if(res.ok) {
                    const data = await res.json();
                    setStrategyName(data.name); setSymbol(data.symbol);
                    const logic = data.logic_configuration || {};
                    setTimeframe(logic.timeframe || "1h"); setQuantity(logic.quantity || 1);
                    setStopLoss(logic.sl || 0); setTakeProfit(logic.tp || 0);
                    const safeConditions = (logic.conditions || []).map((c: any) => ({
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

  const addCondition = () => { setConditions([...conditions, { id: Date.now(), left: { type: 'rsi', params: { length: 14 } }, operator: 'LESS_THAN', right: { type: 'number', params: { value: 30 } } }]); };
  const updateCondition = (id: number, side: 'left' | 'right', field: string, val: any) => { setConditions(conditions.map(c => { if(c.id !== id) return c; if(field === 'type') { const ind = INDICATORS.find(i => i.value === val); const defaultParams: any = {}; ind?.params.forEach(p => defaultParams[p.name] = p.def); return { ...c, [side]: { type: val, params: defaultParams } }; } return { ...c, [side]: { ...c[side], [field]: val } }; })); };
  const updateParam = (id: number, side: 'left' | 'right', paramName: string, val: any) => { setConditions(conditions.map(c => { if(c.id !== id) return c; return { ...c, [side]: { ...c[side], params: { ...c[side].params, [paramName]: val } } }; })); };

  const handleDeploy = async () => {
    if (!session?.user?.email) return alert("Please login first");
    const payload = { email: session.user.email, name: strategyName, symbol, logic: { conditions, timeframe, quantity: Number(quantity), sl: Number(stopLoss), tp: Number(takeProfit) } };
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      let url = apiUrl + '/strategy/create'; let method = 'POST';
      if (editId) { url = apiUrl + '/strategy/' + editId; method = 'PUT'; }
      const res = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if(res.ok) { alert(editId ? "✅ UPDATED!" : "🚀 DEPLOYED!"); router.push('/dashboard'); } else { alert("Failed"); }
    } catch (e) { alert("Server Error."); }
  };

  const handleBacktest = async () => {
    setBacktestLoading(true); setBacktestResult(null);
    const payload = { email: session?.user?.email || "test", name: strategyName, symbol, logic: { conditions, timeframe, quantity: Number(quantity), sl: Number(stopLoss), tp: Number(takeProfit) } };
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(apiUrl + '/strategy/backtest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (data.error) { alert("Error: " + data.error); } else { setBacktestResult(data); }
    } catch(e) { alert("Backtest Failed"); }
    setBacktestLoading(false);
  };

  const IndicatorSelect = ({ side, data, onChange, onParamChange }: any) => {
    if (!data || !data.type) return <div className="text-red-500 text-xs p-2">Invalid Data</div>;
    const selectedDef = INDICATORS.find(i => i.value === data.type);
    return (
        <div className="flex flex-col gap-2 bg-slate-950 p-3 rounded-lg border border-slate-700 min-w-[250px]">
            <div className="relative"><select className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm appearance-none outline-none focus:border-emerald-500" value={data.type} onChange={(e) => onChange('type', e.target.value)}>{INDICATORS.map(ind => (<option key={ind.value} value={ind.value}>{ind.label}</option>))}</select><div className="absolute right-3 top-2.5 pointer-events-none text-slate-500"><Search size={14}/></div></div>
            {selectedDef && selectedDef.params && selectedDef.params.length > 0 && (<div className="grid grid-cols-2 gap-2 mt-1">{selectedDef.params.map((p: any) => (<div key={p.name}><label className="text-[10px] text-slate-500 uppercase">{p.name}</label><input type={p.name === 'source' ? 'text' : 'number'} className="w-full bg-black/30 border border-slate-800 rounded px-2 py-1 text-xs text-cyan-400" value={data.params?.[p.name] || ''} onChange={(e) => onParamChange(p.name, e.target.value)} /></div>))}</div>)}
        </div>
    );
  };

  const formatIST = (isoString: string) => { try { return new Date(isoString).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' }); } catch { return "-"; } };
  const formatPrice = (p: any) => { if (p === undefined || p === null) return "0.00"; return Number(p).toFixed(2); };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 pb-20">
        <div className="col-span-1 space-y-6">
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800"><h3 className="text-lg font-semibold mb-4 text-cyan-400 flex items-center gap-2"><Zap size={18} /> Asset</h3><div className="space-y-4"><div><label className="block text-sm text-slate-400 mb-1">Name</label><input type="text" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div>
          
          {/* LIVE SYMBOL DROPDOWN */}
          <div><label className="block text-sm text-slate-400 mb-1">Pair</label>
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2">
            {symbolList.map(s => (<option key={s} value={s}>{s}</option>))}
          </select></div>
          
          <div><label className="block text-sm text-slate-400 mb-1 flex items-center gap-2"><Clock size={12}/> Timeframe</label><select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2"><option value="1m">1 Min</option><option value="5m">5 Min</option><option value="15m">15 Min</option><option value="1h">1 Hour</option><option value="4h">4 Hour</option></select></div></div></div>
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800"><h3 className="text-lg font-semibold mb-4 text-orange-400 flex items-center gap-2"><AlertTriangle size={18} /> Risk</h3><div className="space-y-4"><div><label className="block text-sm text-slate-400 mb-1">Qty</label><input type="number" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div><div className="grid grid-cols-2 gap-4"><div><label className="block text-sm text-red-400 mb-1">SL %</label><input type="number" step="0.1" value={stopLoss} onChange={(e) => setStopLoss(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div><div><label className="block text-sm text-emerald-400 mb-1">TP %</label><input type="number" step="0.1" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div></div></div></div>
          <div className="flex flex-col gap-3"><button onClick={handleBacktest} disabled={backtestLoading} className="w-full py-4 bg-slate-800 border border-slate-600 rounded-lg font-bold flex items-center justify-center gap-2 hover:bg-slate-700">{backtestLoading ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : <BarChart2 size={18} />} Run Simulation</button><button onClick={handleDeploy} className="w-full py-4 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg font-bold flex items-center justify-center gap-2 hover:scale-105">{editId ? <Save size={18} /> : <Play size={18} />} {editId ? 'Update' : 'Deploy'}</button></div>
        </div>
        
        {/* RIGHT SIDE REMAINS THE SAME */}
    </div>
  );
}

export default function StrategyBuilder() {
  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6"><div className="flex items-center gap-4"><Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-lg transition-colors"><ArrowLeft size={24} className="text-slate-400" /></Link><div><h1 className="text-2xl font-bold flex items-center gap-2">Logic Builder</h1></div></div></header>
      <Suspense fallback={<div className="text-slate-500">Loading...</div>}><BuilderContent /></Suspense>
    </div>
  );
}