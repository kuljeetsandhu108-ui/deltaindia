import os

print("🛡️ Injecting Live API Verification Engine...")

# --- 1. BACKEND: Add the Verification Endpoint to main.py ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: m = f.read()

endpoint_code = """
@app.get("/user/{email}/verify-keys")
async def verify_user_keys(email: str, db: Session = Depends(database.get_db)):
    from app import security
    import ccxt.async_support as ccxt
    import time, hmac, hashlib, requests, json, asyncio
    
    user = crud.get_user_by_email(db, email)
    if not user: return {"error": "User not found"}
    
    res = {"delta": {"status": "UNTESTED"}, "coindcx": {"status": "UNTESTED"}}
    
    # 1. Verify Delta
    if user.delta_api_key and user.delta_api_secret:
        try:
            dk = security.decrypt_value(user.delta_api_key)
            ds = security.decrypt_value(user.delta_api_secret)
            exchange = ccxt.delta({'apiKey': dk, 'secret': ds, 'options': {'defaultType': 'future'}, 'urls': {'api': {'public': 'https://api.india.delta.exchange', 'private': 'https://api.india.delta.exchange'}}})
            await exchange.fetch_balance()
            await exchange.close()
            res["delta"] = {"status": "OK", "error": None}
        except Exception as e:
            err_msg = str(e).split(':')[-1].strip()[:100]
            res["delta"] = {"status": "FAILED", "error": err_msg}
    else:
        res["delta"] = {"status": "FAILED", "error": "Keys not saved in vault yet."}
        
    # 2. Verify CoinDCX
    if user.coindcx_api_key and user.coindcx_api_secret:
        try:
            ck = security.decrypt_value(user.coindcx_api_key)
            cs = security.decrypt_value(user.coindcx_api_secret)
            url = "https://api.coindcx.com/exchange/v1/users/balances"
            payload = {"timestamp": int(time.time() * 1000)}
            json_payload = json.dumps(payload, separators=(',', ':'))
            signature = hmac.new(bytes(cs, 'utf-8'), bytes(json_payload, 'utf-8'), hashlib.sha256).hexdigest()
            headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': ck, 'X-AUTH-SIGNATURE': signature}
            resp = await asyncio.to_thread(requests.post, url, data=json_payload, headers=headers)
            if resp.status_code == 200:
                res["coindcx"] = {"status": "OK", "error": None}
            else:
                msg = resp.json().get('message', f'HTTP Error {resp.status_code}')
                res["coindcx"] = {"status": "FAILED", "error": msg}
        except Exception as e:
            res["coindcx"] = {"status": "FAILED", "error": str(e)[:100]}
    else:
        res["coindcx"] = {"status": "FAILED", "error": "Keys not saved in vault yet."}
        
    return res
"""
if '/verify-keys' not in m:
    m += endpoint_code
    with open('./main.py', 'w') as f: f.write(m)
    os.system('docker cp ./main.py app-backend-1:/app/main.py')


# --- 2. FRONTEND: Inject the UI Card into the Settings Page ---
os.system('docker cp app-frontend-1:/app/app/dashboard/settings/page.tsx ./settings.tsx')
with open('./settings.tsx', 'r') as f: c = f.read()

# Add State variables
state_target = 'const [healthData, setHealthData] = useState<any>(null);'
state_repl = """const [healthData, setHealthData] = useState<any>(null);

  const [keyVerification, setKeyVerification] = useState<any>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const verifyKeys = async () => {
      if (!session?.user?.email) return;
      setIsVerifying(true);
      setKeyVerification(null);
      try {
          const res = await fetch(`https://api.algoease.com/user/${session.user.email}/verify-keys`);
          const data = await res.json();
          setKeyVerification(data);
      } catch (e) {
          setKeyVerification({ error: "Failed to contact backend." });
      }
      setIsVerifying(false);
  };"""

if 'const verifyKeys' not in c:
    c = c.replace(state_target, state_repl)

# Add the UI Card right below the System Radar
ui_target = '            </div>\n        </div>\n\n      </div>'
ui_repl = """            </div>

            {/* LIVE API KEY VERIFICATION CARD */}
            <div className="bg-slate-900 rounded-[2rem] border border-slate-800 p-6 shadow-xl mt-6">
                <h2 className="text-lg font-bold flex items-center gap-2 mb-3"><Lock className="text-blue-400"/> Live Key Verification</h2>
                <p className="text-xs text-slate-400 mb-6">Test if your saved API keys are valid and fully authorized to execute live trades on the exchanges.</p>
                
                <button onClick={verifyKeys} disabled={isVerifying} className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mb-6">
                    {isVerifying ? <RefreshCw size={18} className="animate-spin text-white" /> : <ShieldCheck size={18} className="text-white" />} 
                    {isVerifying ? "Testing Connections..." : "Verify Live Connection"}
                </button>

                {keyVerification && (
                    <div className="space-y-3">
                        {keyVerification.error ? (
                             <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">❌ {keyVerification.error}</div>
                        ) : (
                             <>
                                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-bold text-sm text-white">Delta Exchange</span>
                                        {keyVerification.delta?.status === 'OK' ? <span className="text-emerald-400 text-xs font-bold flex items-center gap-1"><ShieldCheck size={14}/> CONNECTED</span> : <span className="text-red-400 text-xs font-bold flex items-center gap-1"><AlertCircle size={14}/> ERROR</span>}
                                    </div>
                                    {keyVerification.delta?.status !== 'OK' && <p className="text-[11px] text-slate-500 mt-2">{keyVerification.delta?.error}</p>}
                                </div>
                                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-bold text-sm text-white">CoinDCX</span>
                                        {keyVerification.coindcx?.status === 'OK' ? <span className="text-emerald-400 text-xs font-bold flex items-center gap-1"><ShieldCheck size={14}/> CONNECTED</span> : <span className="text-red-400 text-xs font-bold flex items-center gap-1"><AlertCircle size={14}/> ERROR</span>}
                                    </div>
                                    {keyVerification.coindcx?.status !== 'OK' && <p className="text-[11px] text-slate-500 mt-2">{keyVerification.coindcx?.error}</p>}
                                </div>
                             </>
                        )}
                    </div>
                )}
            </div>
        </div>

      </div>"""

if 'LIVE API KEY VERIFICATION CARD' not in c:
    c = c.replace(ui_target, ui_repl)

with open('./settings.tsx', 'w') as f: f.write(c)
os.system('docker cp ./settings.tsx app-frontend-1:/app/app/dashboard/settings/page.tsx')

print("✅ Live Verification Engine safely installed!")
