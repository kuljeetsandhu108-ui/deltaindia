import os

print("🔧 Forcing explicit import of TrendingUp icon...")
os.system('docker cp app-frontend-1:/app/app/dashboard/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# First, clean up any messy failed replacements from the last script
c = c.replace(', TrendingUp }', ' }')
c = c.replace('TrendingUp,', '')

# Now, forcefully inject it on its own dedicated line right below "use client";
if 'import { TrendingUp }' not in c:
    c = c.replace('"use client";', '"use client";\nimport { TrendingUp } from "lucide-react";')

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/page.tsx')
print("✅ Import successfully forced at the top of the file!")
