import time
from data_vault import update_vault

# Expanded list of high-volume altcoins, memes, and layer-1s
top_50_pairs =[
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
    "MATICUSDT", "LTCUSDT", "BCHUSDT", "TRXUSDT", "NEARUSDT",
    "SHIBUSDT", "UNIUSDT", "ATOMUSDT", "XLMUSDT", "ETCUSDT",
    "FILUSDT", "ICPUSDT", "APTUSDT", "ARBUSDT", "OPUSDT",
    "INJUSDT", "RNDRUSDT", "SUIUSDT", "PEPEUSDT", "WLDUSDT",
    "TIAUSDT", "SEIUSDT", "FETUSDT", "STXUSDT", "IMXUSDT",
    "LDOUSDT", "GRTUSDT", "THETAUSDT", "AAVEUSDT", "MKRUSDT",
    "SNXUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT", "GALAUSDT",
    "ENJUSDT", "CHZUSDT", "CRVUSDT", "COMPUSDT", "1INCHUSDT"
]

timeframes = ["1d", "4h", "1h", "15m", "5m"]

print("==================================================")
print("🚀 INITIATING TOP-50 DATA VAULT EXPANSION")
print("==================================================")

for pair in top_50_pairs:
    for tf in timeframes:
        try:
            update_vault(pair, tf, years=4)
        except Exception as e:
            print(f"❌ Error downloading {pair} {tf}: {e}")
        time.sleep(1)

print("\n🎉 EXPANSION COMPLETE!")
