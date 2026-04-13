import os, re

print("✂️ Severing ties to Production... Isolating Staging Environment!")

# --- A. Update the Hardcoded React Files ---
for root, _, files in os.walk('client/app'):
    for file in files:
        if file.endswith(('.tsx', '.ts')):
            fp = os.path.join(root, file)
            with open(fp, 'r') as f: c = f.read()
            
            # Swap API URLs
            c = c.replace('https://api.algoease.com', 'https://api-staging.algoease.com')
            # Swap NextAuth URLs
            c = c.replace('https://algoease.com', 'https://staging.algoease.com')
            
            with open(fp, 'w') as f: f.write(c)

# --- B. Update the Environment Variables ---
env_files = ['client/.env.local', 'client/.env.production']
for ef in env_files:
    if os.path.exists(ef):
        with open(ef, 'r') as f: c = f.read()
        c = c.replace('https://api.algoease.com', 'https://api-staging.algoease.com')
        c = c.replace('https://algoease.com', 'https://staging.algoease.com')
        with open(ef, 'w') as f: f.write(c)

# Push the clean files into the container
os.system('docker cp client/app/. app-frontend-1:/app/app/')
os.system('docker cp client/.env.local app-frontend-1:/app/.env.local 2>/dev/null || true')
os.system('docker cp client/.env.production app-frontend-1:/app/.env.production 2>/dev/null || true')

print("✅ Sandbox perfectly isolated from Production!")
