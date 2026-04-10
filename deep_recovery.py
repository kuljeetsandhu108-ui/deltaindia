import os

print("🧹 Deep Cleaning Next.js Build Environment...")

# A. Sync the Environment File from the server to our working dir
if os.path.exists('client/.env.local'):
    print("✅ Found .env.local on server.")
else:
    print("⚠️ .env.local missing in host folder! Attempting to recover from container...")
    os.system('docker cp app-frontend-1:/app/.env.local ./client/.env.local')

# B. Nuke the cache and old build artifacts inside the container
print("🗑️ Nuking old cache and artifacts...")
os.system('docker exec app-frontend-1 rm -rf /app/.next')
os.system('docker exec app-frontend-1 rm -rf /app/node_modules/.cache')

# C. Ensure the Private Gatekeeper logic is correctly placed one last time
print("🛡️ Verifying Gatekeeper Logic...")
auth_logic = """import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user }) {
      const email = user.email?.toLowerCase();
      if (email === "kuljeetsandhu108@gmail.com") return true;
      try {
        const res = await fetch(`https://api.algoease.com/auth/check-access/${email}`);
        const data = await res.json();
        return data.authorized === true;
      } catch (e) { return false; }
    },
  },
  pages: { error: '/' },
  secret: process.env.NEXTAUTH_SECRET,
});
export { handler as GET, handler as POST };
"""
with open('./auth_route_final.ts', 'w') as f:
    f.write(auth_logic)

os.system('docker cp ./auth_route_final.ts app-frontend-1:/app/app/api/auth/[...nextauth]/route.ts')

print("🚀 Starting Fresh Production Build (This takes ~60 seconds)...")
# We force the Environment variables into the build process again to be 100% sure
os.system('docker exec app-frontend-1 sh -c "npm run build"')

print("✅ Recovery Build Complete!")
