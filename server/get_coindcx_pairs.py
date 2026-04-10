import requests
import json

def probe_coindcx():
    print("\n🔍 STARTING COINDCX PAIR PROBE...\n")
    
    # --- TEST 1: Standard Markets Endpoint ---
    try:
        print("⏳ TEST 1: Checking Standard Markets Endpoint...")
        url1 = "https://api.coindcx.com/exchange/v1/markets_details"
        res1 = requests.get(url1, timeout=10)
        
        if res1.status_code == 200:
            data1 = res1.json()
            print(f"   -> Found {len(data1)} total raw markets.")
            
            # Find ANY pair that has USDT
            usdt_pairs = [m for m in data1 if 'USDT' in str(m.get('coindcx_name', ''))]
            print(f"   -> Found {len(usdt_pairs)} USDT pairs here.")
            
            # Look specifically for B- (Binance Futures) or X- (OkEx) prefixes
            b_pairs = [m['coindcx_name'] for m in usdt_pairs if str(m.get('coindcx_name')).startswith('B-')]
            print(f"   -> Found {len(b_pairs)} 'B-' prefixed pairs.")
            
            if len(usdt_pairs) > 0:
                print("\n   [Sample USDT Market Data]:")
                print(json.dumps(usdt_pairs[0], indent=2))
        else:
            print(f"   ❌ Endpoint returned {res1.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n--------------------------------------------------\n")

    # --- TEST 2: Derivatives/Futures Endpoint ---
    try:
        print("⏳ TEST 2: Checking Derivatives Markets Endpoint...")
        url2 = "https://api.coindcx.com/exchange/v1/derivatives/futures/markets"
        res2 = requests.get(url2, timeout=10)
        
        if res2.status_code == 200:
            data2 = res2.json()
            # If it's a list
            if isinstance(data2, list):
                print(f"   -> Found {len(data2)} total futures markets.")
                if len(data2) > 0:
                    print("\n   [Sample Future Market Data]:")
                    print(json.dumps(data2[0], indent=2))
            elif isinstance(data2, dict):
                print(f"   -> Found dictionary response. Keys: {list(data2.keys())[:5]}...")
        else:
            print(f"   ❌ Endpoint returned {res2.status_code}: {res2.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n🏁 PROBE COMPLETE.\n")

if __name__ == '__main__':
    probe_coindcx()
