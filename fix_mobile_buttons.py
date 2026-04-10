import os

print("📱 Making Strategy Actions visible on mobile...")
os.system('docker cp app-frontend-1:/app/app/dashboard/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# THE FIX: 
# Change 'opacity-0 group-hover:opacity-100' 
# To 'opacity-100 md:opacity-0 md:group-hover:opacity-100'
# This forces visibility on mobile but keeps the hover effect on Desktop.
old_class = 'className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity"'
new_class = 'className="flex gap-3 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity"'

if old_class in content:
    content = content.replace(old_class, new_class)
    
    # Bonus: Make buttons slightly larger for easier mobile tapping
    content = content.replace('size={16}', 'size={18}')
    
    with open('./page.tsx', 'w') as f:
        f.write(content)
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/page.tsx')
    print("✅ Mobile buttons surgically fixed!")
else:
    print("⚠️ Button container class not found. It might have already been updated.")

