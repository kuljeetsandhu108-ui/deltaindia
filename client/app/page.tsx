"use client";
import { signIn, useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { ArrowRight, Lock, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function Home() {
  const { data: session } = useSession();

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center relative overflow-hidden">
      
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-emerald-600/20 rounded-full blur-[120px]" />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="z-10 text-center max-w-3xl px-6"
      >
        <div className="mb-6 flex justify-center">
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-emerald-400 text-sm font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            System Operational
          </span>
        </div>

        <h1 className="text-6xl font-bold tracking-tight text-white mb-6">
          AlgoTrade India <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
            Automate Your Alpha
          </span>
        </h1>

        <p className="text-slate-400 text-lg mb-10">
          Institutional-grade execution for Delta Exchange & CoinDCX.
        </p>

        {session ? (
          <div className="space-y-4">
             <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                <p className="text-white">Welcome, <span className="text-cyan-400">{session.user?.name}</span></p>
             </div>
             
             {/* THIS IS THE FIX: The Link Component */}
             <Link href="/dashboard">
               <button className="px-8 py-4 bg-white text-slate-950 font-bold rounded-lg hover:bg-slate-200 transition-all flex items-center gap-2 mx-auto">
                 Enter Dashboard <ArrowRight size={20} />
               </button>
             </Link>
          </div>
        ) : (
          <button
            onClick={() => signIn("google")}
            className="group relative px-8 py-4 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 transition-all overflow-hidden"
          >
            <span className="relative z-10 flex items-center gap-2">
              Start Trading Now <ArrowRight size={20} />
            </span>
          </button>
        )}
      </motion.div>
    </div>
  );
}