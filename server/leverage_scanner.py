import requests
import urllib3

urllib3.disable_warnings()

def scan_delta():
    print("==================================================")
    print("🔍 SCANNING DELTA EXCHANGE INDIA LEVERAGE LIMITS")
    print("==================================================")
    try:
        res = requests.get("https://api.india.delta.exchange/v2/products", timeout=10)
        products = res.json().get("result", [])
        
        highest_leverage = 0
        btc_lev, eth_lev = 0, 0
        
        for p in products:
            if 'initial_margin' in p:
                # Leverage = 1 / Initial Margin (e.g. 0.01 IM = 100x Leverage)
                lev = int(1 / float(p['initial_margin']))
                if lev > highest_leverage: highest_leverage = lev
                if p['symbol'] == 'BTCUSD' or p['symbol'] == 'BTCUSDT': btc_lev = lev
                if p['symbol'] == 'ETHUSD' or p['symbol'] == 'ETHUSDT': eth_lev = lev

        print(f"🚀 Absolute Maximum Leverage: {highest_leverage}x")
        print(f"🪙  BTC Maximum Leverage: {btc_lev}x")
        print(f"🪙  ETH Maximum Leverage: {eth_lev}x")
        print("✅ Delta successfully scanned.\n")
    except Exception as e:
        print(f"❌ Delta Scan Error: {e}\n")

def scan_coindcx():
    print("==================================================")
    print("🔍 SCANNING COINDCX FUTURES LEVERAGE LIMITS")
    print("==================================================")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        # Fetching from CoinDCX Derivatives endpoint
        res = requests.get("https://api.coindcx.com/exchange/v1/derivatives/futures/markets", headers=headers, verify=False, timeout=10)
        
        if res.status_code == 200:
            markets = res.json()
            highest_leverage = 0
            btc_lev, eth_lev = 0, 0
            
            for m in markets:
                # CoinDCX exposes leverage per pair
                lev = int(m.get('max_leverage', 0))
                sym = m.get('symbol', '')
                
                if lev > highest_leverage: highest_leverage = lev
                if 'BTC' in sym: btc_lev = max(btc_lev, lev)
                if 'ETH' in sym: eth_lev = max(eth_lev, lev)
                
            print(f"🚀 Absolute Maximum Leverage: {highest_leverage}x")
            print(f"🪙  BTC Maximum Leverage: {btc_lev}x")
            print(f"🪙  ETH Maximum Leverage: {eth_lev}x")
            print("✅ CoinDCX successfully scanned.\n")
        else:
            print(f"⚠️ CoinDCX returned Status Code {res.status_code}. They might hide leverage data from unauthorized pings.")
    except Exception as e:
        print(f"❌ CoinDCX Scan Error: {e}\n")

if __name__ == "__main__":
    scan_delta()
    scan_coindcx()
