"use client";

import { useState, useEffect, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Plus, Trash2, Zap, AlertTriangle, Search, Settings2, Save, BarChart2, Clock, List, TrendingUp, Activity, DollarSign, Globe } from 'lucide-react';
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

  // STATE VARIABLES
  const [strategyName, setStrategyName] = useState("My Pro Algo");
  const [broker, setBroker] = useState("DELTA"); // NEW: Broker State
  const [symbol, setSymbol] = useState("");
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

  // FETCH LIVE SYMBOLS (Triggered when Broker changes)
  useEffect(() => {
    const fetchSymbols = async () => {
        try {
            setSymbolList([]); // Clear list while loading
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            // DYNAMIC FETCH BASED ON BROKER
            const res = await fetch(`${apiUrl}/data/symbols?broker=${broker}`);
            if (res.ok) {
                const data = await res.json();
                if (data && data.length > 0) {
                    setSymbolList(data);
                    // Only reset symbol if not editing or if current symbol invalid
                    if (!editId) setSymbol(data[0]); 
                }
            }
        } catch(e) { console.error("Could not fetch symbols", e); }
    };
    fetchSymbols();
  }, [broker]); // Re-run when broker changes

  // LOAD EXISTING STRATEGY
  useEffect(() => {
    if (editId && session?.user?.email) {
        const fetchDetails = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(apiUrl + '/strategy/' + editId);
                if(res.ok) {
                    const data = await res.json();
                    setStrategyName(data.name); 
                    setBroker(data.broker || "DELTA"); // Load Broker
                    setSymbol(data.symbol);
                    
                    const logic = data.logic_configuration || {};
                    setTimeframe(logic.timeframe || "1h"); 
                    setQuantity(logic.quantity || 1);
                    setStopLoss(logic.sl || 0); 
                    setTakeProfit(logic.tp || 0);
                    
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
        // Force Type Casting for TS
        const sideData: any = (side === 'left' ? c.left : c.right);
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
      broker, // Send Broker
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
      broker, // Send Broker to Backtester
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
        
        {/* SETTINGS PANEL */}
        <div className="col-span-1 space-y-6">
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
            <h3 className="text-lg font-semibold mb-4 text-cyan-400 flex items-center gap-2"><Zap size={18} /> Asset</h3>
            <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Name</label>
                  <input type="text" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none focus:border-cyan-500" />
                </div>

                {/* BROKER SELECTOR */}
                <div>
                    <label className="block text-sm text-slate-400 mb-1 flex items-center gap-2"><Globe size={12}/> Broker</label>
                    <select value={broker} onChange={(e) => setBroker(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none font-bold text-yellow-500">
                        <option value="DELTA">Delta Exchange</option>
                        <option value="COINDCX">CoinDCX</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm text-slate-400 mb-1">Pair ({symbolList.length})</label>
                    <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded p-2 outline-none">
                        {symbolList.length > 0 ? symbolList.map(s => (<option key={s} value={s}>{s}</option>)) : <option value="BTCUSD">Loading...</option>}
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
