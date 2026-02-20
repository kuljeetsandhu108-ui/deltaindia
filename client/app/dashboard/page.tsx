"use client";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Plus, Zap, BarChart3, Settings, PlayCircle, Power, Trash2, Terminal, X, Edit3, PauseCircle, Play } from "lucide-react";
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
    setLogs([]); 
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(apiUrl + '/strategies/' + id + '/logs');
        const data = await res.json();
        setLogs(data);
    } catch(e) { console.error(e); }
  };

  const handleToggle = async (id: number) => {
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        await fetch(apiUrl + '/strategies/' + id + '/toggle', { method: 'POST' });
        fetchStrategies(); // Refresh UI
    } catch (e) { alert("Connection Error"); }
  };

  const handleDelete = async (id: number) => {
    if(!confirm("Delete this strategy?")) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(apiUrl + '/strategies/' + id, { method: 'DELETE' });
      setStrategies(strategies.filter((s: any) => s.id !== id));
    } catch (e) { alert("Error"); }
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
            {strategies.map((strat: any) => (
              <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} key={strat.id} className={p-8 rounded-[2rem] border transition-all group relative hover:shadow-2xl hover:shadow-black/50 }>
                <div className="flex justify-between items-start mb-6">
                  {/* PLAY / PAUSE BUTTON */}
                  <div className="flex gap-2">
                    <button onClick={() => handleToggle(strat.id)} className={w-12 h-12 flex items-center justify-center rounded-full transition-all shadow-lg hover:scale-105 }>
                        {strat.is_running ? <PauseCircle size={24} /> : <Play size={24} className="ml-1" />}
                    </button>
                  </div>

                  <div className="flex gap-2">
                    <Link href={'/dashboard/builder?edit=' + strat.id}><button className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:bg-blue-600 hover:text-white transition-all" title="Edit"><Edit3 size={16} /></button></Link>
                    <button onClick={() => fetchLogs(strat.id)} className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:bg-black hover:text-emerald-400 transition-all" title="View Logs"><Terminal size={16} /></button>
                    <button onClick={() => handleDelete(strat.id)} className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:bg-red-900/30 hover:text-red-400 transition-all"><Trash2 size={16} /></button>
                  </div>
                </div>
                
                <h3 className="font-bold text-xl mb-2">{strat.name}</h3>
                <div className="text-slate-400 text-sm mb-6 flex items-center gap-2"><span className="bg-slate-800 px-3 py-1 rounded-full text-xs">{strat.symbol}</span><span className="bg-slate-800 px-3 py-1 rounded-full text-xs">{strat.broker}</span></div>
                
                {strat.is_running ? (
                    <div className="flex items-center gap-3 text-sm font-bold text-emerald-400 bg-emerald-500/10 px-4 py-2 rounded-full w-fit border border-emerald-500/20">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> RUNNING
                    </div>
                ) : (
                    <div className="flex items-center gap-3 text-sm font-bold text-yellow-500 bg-yellow-500/10 px-4 py-2 rounded-full w-fit border border-yellow-500/20">
                        <span className="w-2 h-2 rounded-full bg-yellow-500"></span> PAUSED
                    </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
