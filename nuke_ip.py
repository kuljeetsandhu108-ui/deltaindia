import os, re
for root, _, files in os.walk('client/app'):
    for file in files:
        if file.endswith('.tsx'):
            fp = os.path.join(root, file)
            with open(fp, 'r') as f:
                c = f.read()
            # This finds the variable and permanently replaces it with the secure URL
            c = re.sub(r'const apiUrl = .*?;', 'const apiUrl = "https://api.algoease.com";', c)
            with open(fp, 'w') as f:
                f.write(c)
print("✅ Source code permanently hardcoded with HTTPS!")
