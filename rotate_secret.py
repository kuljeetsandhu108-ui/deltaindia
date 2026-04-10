import os
env_path = 'client/.env.local'
new_secret = os.popen('openssl rand -base64 32').read().strip()
lines = []
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if not line.startswith('NEXTAUTH_SECRET='):
                lines.append(line)
lines.append(f'NEXTAUTH_SECRET="{new_secret}"\n')
with open(env_path, 'w') as f:
    f.writelines(lines)
print("✅ Secret Rotated Successfully.")
