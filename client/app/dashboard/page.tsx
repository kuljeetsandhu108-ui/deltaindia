"use client";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Plus, Zap, BarChart3, Settings, PlayCircle, Power, Trash2, Terminal, X } from "lucide-react";
import Link from 'next/link';

export default function Dashboard() {
  const { data: session } = useSession();
  const [strategies, setStrategies] = useState([]);
  const [selectedStratId, setSelectedStratId] = useState<number | null>(null);
  const [logs, setLogs] = useState([]);

  useEffect(() => { if (session?.user?.email) fetchStrategies(); }, [session]);

  const fetchStrategies = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(apiUrl + '/strategies/' + session?.user?.email);
      const data = await res.json();
      setStrategies(data);
    } catch (e) { console.error("Error"); }
  };

  const fetchLogs = async (id: number) => {
    setSelectedStratId(id);
    setLogs([]); // Clear previous
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(apiUrl + '/strategies/' + id + '/logs');
        const data = await res.json();
        setLogs(data);
    } catch(e) { console.error(e); }
  };

  const handleDelete = async (id: number) => {
    if(!confirm("Delete this strategy?")) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(apiUrl + '/strategies/' + id, { method: 'DELETE' });
      setStrategies(strategies.filter((s: any) => s.id !== id));
    } catch (e) { alert("Error"); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex relative">
      {/* LOG MODAL */}
      <AnimatePresence>
      {selectedStratId && (
        <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-xl overflow-hidden shadow-2xl">
                <div className="flex justify-between items-center p-4 border-b border-slate-800 bg-slate-950">
                    <h3 className="font-mono text-emerald-400 flex items-center gap-2"><Terminal size={18}/> LIVE TERMINAL</h3>
                    <button onClick={() => setSelectedStratId(null)} className="text-slate-500 hover:text-white"><X size={20}/></button>
                </div>
                <div className="h-96 overflow-y-auto p-4 bg-black font-mono text-xs space-y-2">
                    {logs.length === 0 ? <p className="text-slate-600">Waiting for engine ticks...</p> : logs.map((log: any) => (
                        <div key={log.id} className="border-b border-slate-900 pb-1">
                            <span className="text-slate-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span> 
                            <span className={log.level === 'ERROR' ? 'text-red-500 ml-2' : log.level === 'SUCCESS' ? 'text-emerald-400 ml-2' : 'text-blue-400 ml-2'}>
                                {log.level}:
                            </span>
                            <span className="text-slate-300 ml-2">{log.message}</span>
                        </div>
                    ))}
                </div>
                <div className="p-3 bg-slate-950 border-t border-slate-800 flex justify-end">
                    <button onClick={() => fetchLogs(selectedStratId)} className="text-xs text-slate-400 hover:text-white">REFRESH LOGS</button>
                </div>
            </div>
        </motion.div>
      )}
      </AnimatePresence>

      <aside className="w-64 border-r border-slate-800 p-6 hidden md:block"><h2 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent mb-10">AlgoTrade</h2><nav className="space-y-2"><Link href="/dashboard"><button className="w-full flex items-center gap-3 px-4 py-3 bg-slate-900 text-emerald-400 rounded-xl border border-slate-800 transition-all mb-2"><Activity size={20} /> Dashboard</button></Link><Link href="/dashboard/settings"><button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-900 hover:text-white rounded-xl transition-all"><Settings size={20} /> Broker Keys</button></Link></nav></aside>
      <main className="flex-1 p-8">
        <header className="flex justify-between items-center mb-8"><div><h1 className="text-3xl font-bold">Command Center</h1><p className="text-slate-400">Welcome back, {session?.user?.name}</p></div><Link href="/dashboard/builder"><button className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-full font-bold flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all"><Plus size={18} /> New Strategy</button></Link></header>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategies.map((strat: any) => (
              <motion.div key={strat.id} className="bg-slate-900 p-6 rounded-2xl border border-slate-800 hover:border-slate-600 transition-all group relative">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 bg-slate-800 rounded-lg text-cyan-400"><Zap size={20} /></div>
                  <div className="flex gap-2">
                    <button onClick={() => fetchLogs(strat.id)} className="text-slate-500 hover:text-emerald-400" title="View Logs"><Terminal size={18} /></button>
                    <button onClick={() => handleDelete(strat.id)} className="text-slate-500 hover:text-red-400"><Trash2 size={18} /></button>
                  </div>
                </div>
                <h3 className="font-bold text-lg mb-1">{strat.name}</h3>
                <div className="text-slate-400 text-sm mb-4">{strat.symbol} • {strat.broker}</div>
                <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded w-fit"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> RUNNING</div>
              </motion.div>
            ))}
        </div>
      </main>
    </div>
  );
}