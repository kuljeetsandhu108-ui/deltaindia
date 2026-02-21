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
