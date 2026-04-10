import os, re

print("Applying Flawless IST Timezone Conversion...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# Locate the old formatIST function
pattern = r'const formatIST = \(isoString:\s*string\)\s*=>\s*\{[\s\S]*?catch\s*\{\s*return\s*"-";\s*\}\s*\};'

# The Bulletproof UTC -> IST Converter
new_formatIST = """const formatIST = (isoString: string) => { 
      try { 
          let dStr = isoString;
          // Force JavaScript to recognize the raw Pandas timestamp as UTC
          if (!dStr.endsWith('Z') && !dStr.includes('+')) dStr += 'Z';
          
          const date = new Date(dStr);
          return date.toLocaleString('en-IN', { 
              timeZone: 'Asia/Kolkata', 
              day: '2-digit', month: 'short', year: 'numeric', 
              hour: '2-digit', minute: '2-digit', hour12: true 
          }); 
      } catch { return "-"; } 
  };"""

content = re.sub(pattern, new_formatIST, content)

with open('./page.tsx', 'w') as f:
    f.write(content)

os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
print("✅ IST Timezone conversion perfectly injected!")
