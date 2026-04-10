import requests
import json

def get_all_pairs():
    print("... Attempting to fetch ALL CoinDCX Pairs via Ticker API ...")
    try:
        # 1. Use the Public Ticker Endpoint (Lists all active markets)
        url = "https://api.coindcx.com/exchange/ticker"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed. Status Code: {response.status_code}")
            return

        data = response.json()
        
        # 2. Extract pairs
        # The format is [{'market': 'BTCUSDT', ...}, {'market': 'ETHUSDT', ...}]
        all_pairs = []
        for item in data:
            pair = item.get('market')
            # Filter for USDT pairs only
            if pair and pair.endswith('USDT'):
                all_pairs.append(pair)

        # 3. Sort
        all_pairs = sorted(list(set(all_pairs)))

        print(f"\n✅ SUCCESS! Found {len(all_pairs)} Pairs.")
        print("---------------------------------------")
        print(f"First 5: {all_pairs[:5]}")
        print("...")
        print(f"Last 5:  {all_pairs[-5:]}")
        print("---------------------------------------")

    except Exception as e:
        print(f"❌ Crash: {e}")

if __name__ == "__main__":
    get_all_pairs()
