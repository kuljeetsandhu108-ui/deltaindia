import requests
import json

def test_security():
    base_url = "http://localhost:8000/auth/check-access"
    master = "kuljeetsandhu108@gmail.com"
    hacker = "hacker@gmail.com"
    
    print("\n🔍 RUNNING ALGOEASE SECURITY AUDIT...")
    
    # Test Master
    r1 = requests.get(f"{base_url}/{master}")
    print(f"   Admin Check ({master}): {'✅ PASS' if r1.json()['authorized'] else '❌ FAIL'}")
    
    # Test Unauthorized
    r2 = requests.get(f"{base_url}/{hacker}")
    print(f"   Intruder Check ({hacker}): {'✅ BLOCKED' if not r2.json()['authorized'] else '❌ FAILED TO BLOCK'}")
    print("======================================\n")

if __name__ == "__main__":
    test_security()
