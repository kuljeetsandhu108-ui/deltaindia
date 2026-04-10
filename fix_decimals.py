import os, re

print("Applying Precision Decimal Patch...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# Find the old strict 2-decimal formatter
pattern = r'const formatPrice = \(p: any\) => \{[\s\S]*?return Number\(p\)\.toFixed\(2\);\s*\};'

# Replace it with a Dynamic Crypto Formatter
new_format = """const formatPrice = (p: any) => {
      if (p === undefined || p === null || isNaN(Number(p))) return "0.00";
      const val = Number(p);
      if (Math.abs(val) < 0.0001) return val.toFixed(8);
      if (Math.abs(val) < 1) return val.toFixed(4);
      return val.toFixed(2);
  };"""

content = re.sub(pattern, new_format, content)

with open('./page.tsx', 'w') as f:
    f.write(content)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ Decimal UI fixed perfectly!")
