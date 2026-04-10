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
      
      // 1. MASTER ADMIN BYPASS
      if (email === "kuljeetsandhu108@gmail.com") return true;

      // 2. CHECK WHITELIST VIA BACKEND API
      try {
        const res = await fetch(`https://api.algoease.com/auth/check-access/${email}`);
        const data = await res.json();
        if (data.authorized === true) {
            return true;
        } else {
            console.log(`🚫 Access Denied for: ${email}`);
            return false; // Rejects the login
        }
      } catch (error) {
        console.error("Auth Gatekeeper Error:", error);
        return false; // Error in check? Block access for safety.
      }
    },
  },
  pages: {
    error: '/', // Redirect unauthorized users back to the home page
  },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
