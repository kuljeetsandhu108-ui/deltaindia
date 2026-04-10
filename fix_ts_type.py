import os

print("Adding strict TypeScript types to AI matcher...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# Fix the exact TypeScript error by declaring 's' as a string
content = content.replace('data.find(s =>', 'data.find((s: string) =>')

with open('./page.tsx', 'w') as f:
    f.write(content)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ TypeScript error surgically resolved!")
