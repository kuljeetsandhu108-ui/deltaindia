
"use client";
import { TrendingUp } from "lucide-react";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Plus, BarChart2, Trash2, Edit3, Search, Database } from "lucide-react";
import Link from 'next/link';

export default function Dashboard() {
  const { data: session } = useSession();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { if (session?.user?.email) fetchStrategies(); }, [session]);

  const fetchStrategies = async () => {
    try {
      // Hardcoded Secure URL
      const res = await fetch("https://api.algoease.com/strategies/" + session?.user?.email);
      const data = await res.json();
      setStrategies(data);
    } catch (e) { console.error("Error fetching strategies"); }
    setLoading(false);
  };

  const handleDelete = async (id: number) => {
    if(!confirm("Delete this research strategy?")) return;
    try {
      const res = await fetch("https://api.algoease.com/strategies/" + id, { method: 'DELETE' });
      if (res.ok) setStrategies(strategies.filter((s: any) => s.id !== id));
    } catch (e) { alert("Network Error"); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col md:flex-row relative font-sans">
      <aside className="hidden md:block w-72 border-r border-slate-800 p-8 hidden md:block bg-slate-950">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent mb-12">AlgoEase</h2>
        <nav className="space-y-4">
          <Link href="/dashboard"><button className="w-full flex items-center gap-4 px-6 py-4 bg-slate-900 text-indigo-400 rounded-xl border border-slate-800 font-bold"><BookOpen size={20} /> Research</button></Link>
          <Link href="/dashboard/settings"><button className="w-full flex items-center gap-4 px-6 py-4 text-slate-400 hover:bg-slate-900 hover:text-white rounded-xl transition-all font-medium"><Database size={20} /> Data Sources</button></Link>
          <Link href="/dashboard/analyzer"><button className="w-full flex items-center gap-4 px-6 py-4 text-slate-400 hover:bg-slate-900 hover:text-white rounded-xl transition-all font-medium"><TrendingUp size={20} /> Portfolio</button></Link>
        </nav>
      </aside>

      <main className="flex-1 p-10">
        <header className="flex justify-between items-center mb-12">
            <div>
                <h1 className="text-4xl font-bold mb-2 text-white">Research Station</h1>
                <p className="text-slate-400">Quantitative Analysis & Backtesting Terminal</p>
            </div>
            <Link href="/dashboard/builder"><button className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-bold flex items-center gap-3 shadow-lg hover:shadow-indigo-500/30 transition-all"><Plus size={20} /> New Strategy</button></Link>
        </header>
        
        {/* STATS ROW */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div className="p-6 bg-slate-900/50 rounded-2xl border border-slate-800">
                <div className="text-slate-500 text-xs uppercase font-bold mb-2">Saved Strategies</div>
                <div className="text-3xl font-bold text-white">{strategies.length}</div>
            </div>
            <div className="p-6 bg-slate-900/50 rounded-2xl border border-slate-800">
                <div className="text-slate-500 text-xs uppercase font-bold mb-2">Data Vault Status</div>
                <div className="text-3xl font-bold text-emerald-400 flex items-center gap-2"><span className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></span> Active</div>
            </div>
            <div className="p-6 bg-slate-900/50 rounded-2xl border border-slate-800">
                <div className="text-slate-500 text-xs uppercase font-bold mb-2">Compute Engine</div>
                <div className="text-3xl font-bold text-slate-500">Pandas Quant Core</div>
            </div>
        </div>

        <h2 className="text-xl font-bold mb-6 flex items-center gap-2"><Search size={20} className="text-indigo-400"/> Strategy Library</h2>
        
        {strategies.length === 0 && !loading ? (
          <div className="border-2 border-dashed border-slate-800 rounded-[2rem] p-16 flex flex-col items-center justify-center text-slate-500">
            <p className="text-xl mb-4">No strategies found.</p>
            <Link href="/dashboard/builder"><button className="text-indigo-400 hover:text-white font-bold underline">Create your first Alpha Strategy</button></Link>
          </div>
        ) : (
          <div className="grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategies.map((strat: any) => (
              <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} key={strat.id} className="p-6 rounded-2xl border border-slate-800 bg-slate-900 hover:border-indigo-500/50 transition-all group">
                <div className="flex justify-between items-start mb-4">
                  <div className="bg-slate-800/50 p-3 rounded-lg text-indigo-400"><BarChart2 size={24}/></div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Link href={'/dashboard/builder?edit=' + strat.id}><button className="p-2 rounded-lg bg-slate-800 hover:bg-white hover:text-black transition-all"><Edit3 size={16} /></button></Link>
                    <button onClick={() => handleDelete(strat.id)} className="p-2 rounded-lg bg-slate-800 hover:bg-red-500 hover:text-white transition-all"><Trash2 size={16} /></button>
                  </div>
                </div>
                <h3 className="font-bold text-lg text-white mb-1 truncate">{strat.name}</h3>
                <div className="text-slate-500 text-xs mb-6 flex items-center gap-2">
                    <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800">{strat.symbol}</span>
                    <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800">{strat.broker}</span>
                </div>
                <Link href={'/dashboard/builder?edit=' + strat.id}>
                    <button className="w-full py-3 rounded-xl bg-indigo-600/10 text-indigo-400 font-bold hover:bg-indigo-600 hover:text-white transition-all flex items-center justify-center gap-2">
                        Simulate & Analyze
                    </button>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </main>

      {/* MOBILE BOTTOM NAV */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800 px-6 py-3 flex justify-around items-center z-50 backdrop-blur-md">
        <Link href="/dashboard" className="flex flex-col items-center gap-1 text-indigo-400"><BookOpen size={20}/><span className="text-[10px] font-bold">Research</span></Link>
        <Link href="/dashboard/analyzer" className="flex flex-col items-center gap-1 text-slate-400"><TrendingUp size={20}/><span className="text-[10px]">Portfolio</span></Link>
        <Link href="/dashboard/settings" className="flex flex-col items-center gap-1 text-slate-400"><Database size={20}/><span className="text-[10px]">Data</span></Link>
      </nav>

    </div>
  );
}
