import os, re
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# This regex finds the messy logic object (even with duplicates) and replaces it with the perfect one
pattern = r'logic:\s*\{\s*conditions,\s*timeframe,\s*quantity:\s*Number\(quantity\),\s*sl:\s*Number\(stopLoss\),\s*tp:\s*Number\(takeProfit\)[^\}]*\}'
good_logic = 'logic: { conditions, timeframe, quantity: Number(quantity), sl: Number(stopLoss), tp: Number(takeProfit), side, tradeMode, state: "WAITING" }'

content = re.sub(pattern, good_logic, content)

with open('./page.tsx', 'w') as f:
    f.write(content)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Payload duplicates cleaned perfectly!")
