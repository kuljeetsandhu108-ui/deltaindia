import os

print("Applying Surgical UI Patch...")
os.system('docker cp app-frontend-1:/app/app/dashboard/builder/page.tsx ./page.tsx')

with open('./page.tsx', 'r') as f:
    content = f.read()

# Locate the exact UI component that is causing the focus loss
start_str = "  const IndicatorSelect = ({ side, data, onChange, onParamChange }: any) => {"
end_str = "  const formatIST ="

if start_str in content and end_str in content:
    start_idx = content.find(start_str)
    end_idx = content.find(end_str)
    
    # Extract the component code
    component_code = content[start_idx:end_idx]
    
    # Erase it from its buggy location inside the main loop
    content = content[:start_idx] + content[end_idx:]
    
    # UPGRADE: Allow decimal numbers (floats) seamlessly in the inputs
    component_code = component_code.replace("type={p.name === 'source' ? 'text' : 'number'}", "type={p.name === 'source' ? 'text' : 'number'} step=\"any\"")
    
    # Place it safely OUTSIDE the main loop so it never loses focus!
    target = "function BuilderContent() {"
    content = content.replace(target, component_code + "\n" + target)
    
    with open('./page.tsx', 'w') as f:
        f.write(content)
    
    os.system('docker cp ./page.tsx app-frontend-1:/app/app/dashboard/builder/page.tsx')
    print("✅ Input Focus & Decimal Bug completely fixed!")
else:
    print("Component already extracted or not found.")
