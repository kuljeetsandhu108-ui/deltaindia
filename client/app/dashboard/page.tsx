"use client";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Plus, Zap, BarChart3, Settings, PlayCircle, Power, Trash2 } from "lucide-react";
import Link from 'next/link';

export default function Dashboard() {
  const { data: session } = useSession();
  const [strategies, setStrategies] = useState([]);

  useEffect(() => {
    if (session?.user?.email) { fetchStrategies(); }
  }, [session]);

  const fetchStrategies = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      // SAFE CODE: Simple addition instead of backticks
      const res = await fetch(apiUrl + '/strategies/' + session?.user?.email);
      const data = await res.json();
      setStrategies(data);
    } catch (e) { console.error("Failed to fetch strategies"); }
  };

  const handleDelete = async (id: number) => {
    if(!confirm("Are you sure you want to stop and delete this strategy?")) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      // SAFE CODE
      await fetch(apiUrl + '/strategies/' + id, { method: 'DELETE' });
      // Remove from UI instantly
      setStrategies(strategies.filter((s: any) => s.id !== id));
    } catch (e) { alert("Error deleting strategy"); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex">
      <aside className="w-64 border-r border-slate-800 p-6 hidden md:block"><h2 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent mb-10">AlgoTrade</h2><nav className="space-y-2"><Link href="/dashboard"><button className="w-full flex items-center gap-3 px-4 py-3 bg-slate-900 text-emerald-400 rounded-xl border border-slate-800 transition-all mb-2"><Activity size={20} /> Dashboard</button></Link><Link href="/dashboard/settings"><button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-900 hover:text-white rounded-xl transition-all"><Settings size={20} /> Broker Keys</button></Link></nav></aside>
      <main className="flex-1 p-8">
        <header className="flex justify-between items-center mb-8"><div><h1 className="text-3xl font-bold">Command Center</h1><p className="text-slate-400">Welcome back, {session?.user?.name}</p></div><Link href="/dashboard/builder"><button className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-full font-bold flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all"><Plus size={18} /> New Strategy</button></Link></header>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10"><div className="p-6 bg-slate-900 rounded-2xl border border-slate-800"><div className="text-slate-400 mb-2 flex items-center gap-2"><Activity size={16}/> Active Algos</div><div className="text-3xl font-bold text-white">{strategies.length} <span className="text-sm text-slate-500 font-normal">running</span></div></div><div className="p-6 bg-slate-900 rounded-2xl border border-slate-800"><div className="text-slate-400 mb-2 flex items-center gap-2"><BarChart3 size={16}/> Total Volume</div><div className="text-3xl font-bold text-white">₹0.00</div></div><div className="p-6 bg-slate-900 rounded-2xl border border-slate-800 relative overflow-hidden"><div className="absolute right-0 top-0 p-4 opacity-10"><Zap size={60} /></div><div className="text-slate-400 mb-2">System Status</div><div className="text-emerald-400 font-bold flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Online</div></div></div>
        <h2 className="text-xl font-semibold mb-4">Your Strategies</h2>
        {strategies.length === 0 ? (<div className="border border-dashed border-slate-800 rounded-2xl p-12 flex flex-col items-center justify-center text-slate-500"><div className="bg-slate-900 p-4 rounded-full mb-4"><PlayCircle size={32} className="text-slate-400" /></div><p className="text-lg">No algorithms running yet.</p><Link href="/dashboard/builder"><button className="mt-4 text-emerald-400 hover:text-emerald-300 font-semibold">+ Create New Algo</button></Link></div>) : (<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">{strategies.map((strat: any) => (<motion.div initial={{opacity:0}} animate={{opacity:1}} key={strat.id} className="bg-slate-900 p-6 rounded-2xl border border-slate-800 hover:border-slate-600 transition-all group"><div className="flex justify-between items-start mb-4"><div className="p-2 bg-slate-800 rounded-lg text-cyan-400"><Zap size={20} /></div><div className="flex gap-2"><button className="text-slate-500 hover:text-white"><Power size={18} /></button><button onClick={() => handleDelete(strat.id)} className="text-slate-500 hover:text-red-400"><Trash2 size={18} /></button></div></div><h3 className="font-bold text-lg mb-1">{strat.name}</h3><div className="text-slate-400 text-sm mb-4">{strat.symbol} • {strat.broker}</div><div className="flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded w-fit"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> RUNNING</div></motion.div>))}</div>)}
      </main>
    </div>
  );
}