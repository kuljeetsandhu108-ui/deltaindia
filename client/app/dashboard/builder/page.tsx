"use client";
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Plus, Trash2, Zap } from 'lucide-react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';

export default function StrategyBuilder() {
  const { data: session } = useSession();
  const [strategyName, setStrategyName] = useState("My Alpha Algo 1");
  const [symbol, setSymbol] = useState("BTCUSD");
  const [conditions, setConditions] = useState([{ id: 1, indicator: 'EMA', period: '20', operator: 'CROSSES_ABOVE', value: 'EMA 50' }]);

  const addCondition = () => { setConditions([...conditions, { id: conditions.length + 1, indicator: 'RSI', period: '14', operator: 'LESS_THAN', value: '30' }]); };
  const removeCondition = (id: number) => { setConditions(conditions.filter(c => c.id !== id)); };

  const handleDeploy = async () => {
    if (!session?.user?.email) return alert("Please login first");
    const payload = { email: session.user.email, name: strategyName, symbol: symbol, logic: { conditions: conditions } };
    try {
      // FIXED: Uses Environment Variable
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(\\/strategy/create\, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = await res.json();
      if(res.ok) { alert("🚀 STRATEGY DEPLOYED! ID: " + data.id + "\\nEngine is now watching " + symbol); } 
      else { alert("Deployment Failed"); }
    } catch (e) { alert("Server Error."); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-4"><Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-lg transition-colors"><ArrowLeft size={24} className="text-slate-400" /></Link><div><h1 className="text-2xl font-bold flex items-center gap-2">Logic Builder</h1></div></div>
        <button onClick={handleDeploy} className="px-6 py-2 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg font-bold flex items-center gap-2 hover:scale-105 transition-transform"><Play size={18} /> Deploy Live</button>
      </header>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="space-y-6"><div className="bg-slate-900 p-6 rounded-xl border border-slate-800"><h3 className="text-lg font-semibold mb-4 text-cyan-400 flex items-center gap-2"><Zap size={18} /> Asset Configuration</h3><div className="space-y-4"><div><label className="block text-sm text-slate-400 mb-1">Strategy Name</label><input type="text" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div><div><label className="block text-sm text-slate-400 mb-1">Pair</label><select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2"><option value="BTCUSD">BTC/USD</option><option value="ETHUSD">ETH/USD</option></select></div></div></div></div>
        <div className="col-span-2 space-y-4"><h3 className="text-lg font-semibold text-emerald-400">Entry Conditions (Buy)</h3><AnimatePresence>{conditions.map((condition, index) => (<motion.div key={condition.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center gap-4"><div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-sm font-bold text-slate-500">{index === 0 ? 'IF' : 'AND'}</div><div className="bg-slate-950 border border-slate-700 rounded px-3 py-1 text-sm">{condition.indicator}</div><span className="text-slate-500 text-sm">is</span><div className="text-emerald-400 font-medium">{condition.operator}</div><div className="bg-slate-950 border border-slate-700 rounded px-3 py-1 text-sm">{condition.value}</div><button onClick={() => removeCondition(condition.id)} className="ml-auto text-red-400 hover:bg-red-400/10 p-2 rounded"><Trash2 size={16} /></button></motion.div>))}</AnimatePresence><button onClick={addCondition} className="w-full py-4 border-2 border-dashed border-slate-800 rounded-xl text-slate-600 hover:border-slate-600 flex items-center justify-center gap-2"><Plus size={20} /> Add Condition</button></div>
      </div>
    </div>
  );
}
