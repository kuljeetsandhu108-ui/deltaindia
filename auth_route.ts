import NextAuth from "next-auth";
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
      
      // 1. MASTER ADMIN ALWAYS ALLOWED
      if (email === "kuljeetsandhu108@gmail.com") {
          console.log("👑 Master Admin Login: Access Granted");
          return true;
      }

      // 2. CHECK WHITELIST VIA BACKEND
      try {
        console.log(`🔐 Gatekeeper checking access for: ${email}`);
        const res = await fetch(`https://api.algoease.com/auth/check-access/${email}`);
        const data = await res.json();
        
        if (data.authorized === true) {
            console.log(`✅ Whitelist Match: Access Granted to ${email}`);
            return true;
        } else {
            console.log(`🚫 SECURITY BREACH: Access Denied to ${email}`);
            return false; // This blocks the login completely
        }
      } catch (error) {
        console.error("⚠️ Gatekeeper API Error:", error);
        return false; // Block on error for maximum safety
      }
    },
  },
  pages: {
    error: '/', 
  },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
