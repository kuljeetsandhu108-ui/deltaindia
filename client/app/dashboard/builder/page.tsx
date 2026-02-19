"use client";
import { useState, useEffect, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Plus, Trash2, Zap, AlertTriangle, Search, Settings2, Save } from 'lucide-react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { INDICATORS } from '@/lib/indicators';
import { useSearchParams, useRouter } from 'next/navigation';

// 1. WE MOVED THE LOGIC INTO THIS INNER COMPONENT
function BuilderContent() {
  const { data: session } = useSession();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const editId = searchParams.get('edit'); 

  const [strategyName, setStrategyName] = useState("My Alpha Algo 1");
  const [symbol, setSymbol] = useState("BTCUSD");
  const [quantity, setQuantity] = useState(1);
  const [stopLoss, setStopLoss] = useState(1.0);
  const [takeProfit, setTakeProfit] = useState(2.0);
  
  const [conditions, setConditions] = useState([
    { id: 1, 
      left: { type: 'rsi', params: { length: 14 } }, 
      operator: 'CROSSES_ABOVE', 
      right: { type: 'number', params: { value: 30 } } 
    }
  ]);

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
                    const logic = data.logic_configuration;
                    setQuantity(logic.quantity || 1);
                    setStopLoss(logic.sl || 0);
                    setTakeProfit(logic.tp || 0);
                    setConditions(logic.conditions || []);
                }
            } catch (e) { console.error(e); }
        };
        fetchDetails();
    }
  }, [editId, session]);

  const addCondition = () => {
    setConditions([...conditions, { 
        id: Date.now(), 
        left: { type: 'rsi', params: { length: 14 } }, 
        operator: 'LESS_THAN', 
        right: { type: 'number', params: { value: 30 } } 
    }]);
  };

  const updateCondition = (id: number, side: 'left' | 'right', field: string, val: any) => {
    setConditions(conditions.map(c => {
        if(c.id !== id) return c;
        if(field === 'type') {
            const ind = INDICATORS.find(i => i.value === val);
            const defaultParams: any = {};
            ind?.params.forEach(p => defaultParams[p.name] = p.def);
            // @ts-ignore
            return { ...c, [side]: { type: val, params: defaultParams } };
        }
        // @ts-ignore
        return { ...c, [side]: { ...c[side], [field]: val } };
    }));
  };

  const updateParam = (id: number, side: 'left' | 'right', paramName: string, val: any) => {
    setConditions(conditions.map(c => {
        if(c.id !== id) return c;
        // @ts-ignore
        return { ...c, [side]: { ...c[side], params: { ...c[side].params, [paramName]: val } } };
    }));
  };

  const handleDeploy = async () => {
    if (!session?.user?.email) return alert("Please login first");
    const payload = { 
        email: session.user.email, name: strategyName, symbol, 
        logic: { conditions, quantity: Number(quantity), sl: Number(stopLoss), tp: Number(takeProfit) } 
    };
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      let url = apiUrl + '/strategy/create';
      let method = 'POST';

      if (editId) {
          url = apiUrl + '/strategy/' + editId;
          method = 'PUT';
      }

      const res = await fetch(url, { 
        method: method, 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(payload) 
      });
      
      if(res.ok) { 
          alert(editId ? "✅ STRATEGY UPDATED!" : "🚀 STRATEGY DEPLOYED!");
          router.push('/dashboard'); 
      } else { alert("Operation Failed"); }
    } catch (e) { alert("Server Error."); }
  };

  const IndicatorSelect = ({ side, data, onChange, onParamChange }: any) => {
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
                            <input type={p.name === 'source' ? 'text' : 'number'} className="w-full bg-black/30 border border-slate-800 rounded px-2 py-1 text-xs text-cyan-400" value={data.params?.[p.name] || ''} onChange={(e) => onParamChange(p.name, e.target.value)} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="col-span-1 space-y-6">
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800"><h3 className="text-lg font-semibold mb-4 text-cyan-400 flex items-center gap-2"><Zap size={18} /> Asset</h3><div className="space-y-4"><div><label className="block text-sm text-slate-400 mb-1">Name</label><input type="text" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div><div><label className="block text-sm text-slate-400 mb-1">Pair</label><select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2"><option value="BTCUSD">BTC/USD</option><option value="ETHUSD">ETH/USD</option></select></div></div></div>
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800"><h3 className="text-lg font-semibold mb-4 text-orange-400 flex items-center gap-2"><AlertTriangle size={18} /> Risk</h3><div className="space-y-4"><div><label className="block text-sm text-slate-400 mb-1">Qty</label><input type="number" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div><div className="grid grid-cols-2 gap-4"><div><label className="block text-sm text-red-400 mb-1">SL %</label><input type="number" step="0.1" value={stopLoss} onChange={(e) => setStopLoss(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div><div><label className="block text-sm text-emerald-400 mb-1">TP %</label><input type="number" step="0.1" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded p-2" /></div></div></div></div>
          
          {/* DEPLOY BUTTON MOVED HERE FOR MOBILE LAYOUT */}
          <button onClick={handleDeploy} className="w-full py-4 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg font-bold flex items-center justify-center gap-2 hover:scale-105 transition-transform">
            {editId ? <Save size={18} /> : <Play size={18} />} {editId ? 'Update Strategy' : 'Deploy Live'}
          </button>
        </div>

        <div className="col-span-3 space-y-4"><h3 className="text-lg font-semibold text-emerald-400 flex items-center gap-2"><Settings2 size={18}/> Entry Logic</h3><div className="space-y-4">{conditions.map((c, i) => (<motion.div key={c.id} initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} className="flex flex-col md:flex-row items-center gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800 relative"><div className="text-slate-500 font-bold bg-slate-800 w-10 h-10 rounded-full flex items-center justify-center shrink-0">{i === 0 ? 'IF' : 'AND'}</div><IndicatorSelect data={c.left} onChange={(f: string, v: any) => updateCondition(c.id, 'left', f, v)} onParamChange={(p: string, v: any) => updateParam(c.id, 'left', p, v)} /><select className="bg-slate-950 text-emerald-400 font-bold border border-slate-700 rounded px-3 py-2 outline-none" value={c.operator} onChange={(e) => { const newConds = [...conditions]; newConds.find(x => x.id === c.id)!.operator = e.target.value; setConditions(newConds); }}><option value="CROSSES_ABOVE">Crosses Above</option><option value="CROSSES_BELOW">Crosses Below</option><option value="GREATER_THAN">Greater Than</option><option value="LESS_THAN">Less Than</option></select><IndicatorSelect data={c.right} onChange={(f: string, v: any) => updateCondition(c.id, 'right', f, v)} onParamChange={(p: string, v: any) => updateParam(c.id, 'right', p, v)} /><button onClick={() => setConditions(conditions.filter(x => x.id !== c.id))} className="absolute top-2 right-2 text-slate-600 hover:text-red-400"><Trash2 size={16}/></button></motion.div>))}</div><button onClick={addCondition} className="w-full py-4 border-2 border-dashed border-slate-800 rounded-xl text-slate-600 hover:border-slate-600 flex items-center justify-center gap-2 transition-all"><Plus size={20} /> Add Logic Block</button></div>
    </div>
  );
}

// 2. MAIN COMPONENT (THE FIX)
// We wrap the Logic in Suspense so Next.js doesn't crash during build
export default function StrategyBuilder() {
  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-4"><Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-lg transition-colors"><ArrowLeft size={24} className="text-slate-400" /></Link><div><h1 className="text-2xl font-bold flex items-center gap-2">Logic Builder</h1></div></div>
      </header>
      
      {/* THE MAGIC WRAPPER */}
      <Suspense fallback={<div className="text-slate-500">Loading Builder...</div>}>
        <BuilderContent />
      </Suspense>
    </div>
  );
}
