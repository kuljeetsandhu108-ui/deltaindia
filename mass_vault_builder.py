import time
from data_vault import update_vault

# The Top 15 Highest Volume Crypto Assets
top_pairs = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
    "MATICUSDT", "LTCUSDT", "BCHUSDT", "TRXUSDT", "NEARUSDT"
]

# The essential institutional timeframes
timeframes = ["1d", "4h", "1h", "15m", "5m"]

print("==================================================")
print("🚀 INITIATING MASS DATA VAULT BUILDER")
print("==================================================")
print(f"Preparing to download {len(top_pairs) * len(timeframes)} massive historical datasets...\n")

for pair in top_pairs:
    for tf in timeframes:
        try:
            # We fetch 4 years of data for each. 
            # (Note: 5m timeframe over 4 years is ~420,000 candles per coin!)
            update_vault(pair, tf, years=4)
        except Exception as e:
            print(f"❌ Error downloading {pair} {tf}: {e}")
        time.sleep(2) # Safe pause between downloads to prevent IP bans

print("\n🎉 MASS VAULT BUILD COMPLETE!")
print("All major pairs and timeframes are now stored locally.")
