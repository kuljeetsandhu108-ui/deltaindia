import os

# Pull the broken file
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    lines = f.readlines()

clean_lines = []
for line in lines:
    # Erase all traces of these variables so we start fresh
    if 'const [side, setSide]' in line or 'const [tradeMode, setTradeMode]' in line:
        continue
    clean_lines.append(line)

content = "".join(clean_lines)

# Inject them back EXACTLY ONCE right below the broker variable
content = content.replace('const [broker, setBroker] = useState("DELTA");', 'const [broker, setBroker] = useState("DELTA");\n  const [side, setSide] = useState("BUY");\n  const [tradeMode, setTradeMode] = useState("PAPER");')

with open('./page.tsx', 'w') as f:
    f.write(content)

# Push the cleaned file back into the container
os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("Duplicates cleaned successfully!")
