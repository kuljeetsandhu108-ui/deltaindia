import os, re

print("⚓ Anchoring the Data Vault strictly to January 1, 2021...")
os.system('docker cp app-backend-1:/app/fast_vault.py ./fast_vault.py')

with open('./fast_vault.py', 'r') as f:
    c = f.read()

# Locate the old "rolling 5 years" math
target = r'start_ms = now_ms - \(5 \* 365 \* 24 \* 60 \* 60 \* 1000\)[\s\S]*?(?=\n\s*df = pd\.DataFrame\(\))'

# Replace it with the exact Jan 1, 2021 Epoch Anchor
replacement = """# Exactly January 1, 2021 00:00:00 UTC
    start_ms = 1609459200000"""

c = re.sub(target, replacement, c)

with open('./fast_vault.py', 'w') as f:
    f.write(c)

os.system('docker cp ./fast_vault.py app-backend-1:/app/fast_vault.py')
print("✅ Vault Data anchored to 2021 successfully!")
