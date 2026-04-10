import os
import pandas as pd

print("==================================================")
print("🩺 ALGOEASE BACKTEST DATA DOCTOR")
print("==================================================")

vault_dir = "/app/vault"
if not os.path.exists(vault_dir):
    print("❌ Vault directory does not exist yet.")
else:
    files = os.listdir(vault_dir)
    if not files:
        print("⚠️ Vault is empty. Run 'python3 data_vault.py' first.")
    else:
        for file in files:
            if file.endswith('.parquet'):
                df = pd.read_parquet(os.path.join(vault_dir, file))
                print(f"📁 VAULT FILE FOUND: {file}")
                print(f"   📊 Total Candles Ready: {len(df):,}")
                print(f"   🕒 Oldest Data: {df.iloc[0]['timestamp']}")
                print(f"   🕒 Newest Data: {df.iloc[-1]['timestamp']}")
                print("-" * 50)
print("✅ Diagnostics Complete.")
