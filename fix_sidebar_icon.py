import os, re

print("🔧 Fixing missing TrendingUp icon import...")
os.system('docker cp app-frontend-1:/app/app/dashboard/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    c = f.read()

# Find the lucide-react import and add TrendingUp to it
if 'TrendingUp' not in c:
    # We replace "Database }" with "Database, TrendingUp }"
    c = c.replace('Database } from "lucide-react"', 'Database, TrendingUp } from "lucide-react"')

with open('./page.tsx', 'w') as f:
    f.write(c)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/page.tsx')
print("✅ Import fixed!")
