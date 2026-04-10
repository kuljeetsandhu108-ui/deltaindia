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
      
      // MASTER ADMIN BYPASS
      if (email === "kuljeetsandhu108@gmail.com") return true;

      try {
        const res = await fetch(`https://api.algoease.com/auth/check-access/${email}`);
        const data = await res.json();
        // Fixed: using lowercase true for JavaScript
        return data.authorized === true || data.authorized === "true";
      } catch (e) { 
        return false; 
      }
    },
  },
  pages: { error: '/' },
  secret: process.env.NEXTAUTH_SECRET,
});
export { handler as GET, handler as POST };
