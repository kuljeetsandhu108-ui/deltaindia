
"use client";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { Wallet, TrendingUp, AlertTriangle } from "lucide-react";

export default function Analyzer() {
  const { data: session } = useSession();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session?.user?.email) fetchPortfolio();
  }, [session]);

  const fetchPortfolio = async () => {
    try {
        const res = await fetch(`https://api.algoease.com/user/${session?.user?.email}/portfolio`);
        if (res.ok) setData(await res.json());
    } catch(e) {}
    setLoading(false);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  if (loading) return <div className="p-10 text-slate-500">Loading Portfolio...</div>;

  return (
    <div className="p-10 text-white min-h-screen">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-3">
            <Wallet className="text-emerald-400"/> Portfolio Command Center
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800">
                <div className="text-slate-500 text-xs uppercase font-bold mb-2">Net Worth (USDT)</div>
                <div className="text-4xl font-bold text-white">${data?.total_usdt?.toFixed(2) || "0.00"}</div>
            </div>
            <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800">
                <div className="text-slate-500 text-xs uppercase font-bold mb-2">Net Worth (INR)</div>
                <div className="text-4xl font-bold text-emerald-400">₹{data?.total_inr?.toFixed(2) || "0.00"}</div>
            </div>
            <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800">
                <div className="text-slate-500 text-xs uppercase font-bold mb-2">Active Positions</div>
                <div className="text-4xl font-bold text-blue-400">{data?.positions?.length || 0}</div>
            </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h3 className="font-bold text-lg mb-4">Asset Allocation</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie data={data?.assets} cx="50%" cy="50%" innerRadius={60} outerRadius={80} fill="#8884d8" paddingAngle={5} dataKey="amount">
                                {data?.assets?.map((entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{backgroundColor: '#0f172a', border: 'none'}} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h3 className="font-bold text-lg mb-4">Open Positions</h3>
                {data?.positions?.length === 0 ? (
                    <div className="text-slate-500 text-center py-10">No active trades found.</div>
                ) : (
                    <div className="space-y-4">
                        {data?.positions?.map((p: any, i: number) => (
                            <div key={i} className="flex justify-between items-center p-4 bg-slate-950 rounded-xl border border-slate-800">
                                <div>
                                    <div className="font-bold text-white">{p.symbol}</div>
                                    <div className="text-xs text-slate-500">{p.broker} • Size: {p.size}</div>
                                </div>
                                <div className={`font-mono font-bold ${p.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {p.pnl >= 0 ? '+' : ''}${Number(p.pnl).toFixed(2)}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    </div>
  );
}
