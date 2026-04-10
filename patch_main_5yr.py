import os, re
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: m = f.read()

target = r'        vault_path = f"/app/vault/\{clean_symbol\}_\{tf\}\.parquet"[\s\S]*?(?=        if df is None or df\.empty:)'
replacement = """        from fast_vault import ensure_5_years_sync
        
        # 🛡️ THE 5-YEAR GUARANTEE: This forces the server to instantly fetch/verify 5 years of data
        df = ensure_5_years_sync(clean_symbol, tf)
        
        s_date = strat.logic.get('startDate')
        e_date = strat.logic.get('endDate')
        if s_date and e_date:
            df = df[(df['timestamp'] >= pd.to_datetime(s_date)) & (df['timestamp'] <= pd.to_datetime(e_date) + pd.Timedelta(days=1))]
"""
m = re.sub(target, replacement, m)
with open('./main.py', 'w') as f: f.write(m)
os.system('docker cp ./main.py app-backend-1:/app/main.py')
