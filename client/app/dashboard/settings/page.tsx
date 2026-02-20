"use client";
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Save, Lock, ShieldCheck, AlertCircle, Eye, EyeOff, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';

export default function BrokerSettings() {
  const { data: session } = useSession();
  const [showDelta, setShowDelta] = useState(false);
  const [showDcx, setShowDcx] = useState(false);
  const [deltaStatus, setDeltaStatus] = useState("disconnected");
  
  const [formData, setFormData] = useState({
    deltaKey: "", deltaSecret: "", dcxKey: "", dcxSecret: ""
  });

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
      
      const res = await fetch(`${apiUrl}/user/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        if(broker === 'Delta') setDeltaStatus("connected");
        alert(`Success! ${broker} Keys Encrypted and Saved.`);
      } else { alert("Error saving keys."); }
    } catch (error) { alert("Server Connection Error."); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <header className="flex justify-between items-center mb-10 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-lg transition-colors"><ArrowLeft size={24} className="text-slate-400" /></Link>
          <div><h1 className="text-2xl font-bold flex items-center gap-2">Broker Connections</h1><p className="text-slate-500 text-sm">Keys are AES-256 Encrypted.</p></div>
        </div>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
        {/* DELTA EXCHANGE */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
            <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white">D</div><div><h3 className="font-bold text-lg">Delta Exchange</h3></div></div>
          </div>
          <div className="p-6 space-y-4">
            <div><label className="block text-sm text-slate-400 mb-1">API Key</label><input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 outline-none" onChange={(e) => setFormData({...formData, deltaKey: e.target.value})} /></div>
            <div className="relative"><label className="block text-sm text-slate-400 mb-1">API Secret</label><input type={showDelta ? "text" : "password"} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 outline-none" onChange={(e) => setFormData({...formData, deltaSecret: e.target.value})} /><button onClick={() => setShowDelta(!showDelta)} className="absolute right-3 top-9 text-slate-500 hover:text-white">{showDelta ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
            <button onClick={() => handleSave('Delta')} className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 text-white py-3 rounded-lg font-bold transition-all"><Save size={18} /> Save Credentials</button>
          </div>
        </motion.div>
        
        {/* COINDCX */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
            <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white">C</div><div><h3 className="font-bold text-lg">CoinDCX</h3></div></div>
          </div>
          <div className="p-6 space-y-4">
            <div><label className="block text-sm text-slate-400 mb-1">API Key</label><input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 outline-none" onChange={(e) => setFormData({...formData, dcxKey: e.target.value})} /></div>
            <div className="relative"><label className="block text-sm text-slate-400 mb-1">API Secret</label><input type={showDcx ? "text" : "password"} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 outline-none" onChange={(e) => setFormData({...formData, dcxSecret: e.target.value})} /><button onClick={() => setShowDcx(!showDcx)} className="absolute right-3 top-9 text-slate-500 hover:text-white">{showDcx ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
            <button onClick={() => handleSave('CoinDCX')} className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-lg font-bold transition-all"><Save size={18} /> Save Credentials</button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}