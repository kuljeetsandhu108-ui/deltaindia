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
      if (email === "kuljeetsandhu108@gmail.com") return true;
      try {
        const res = await fetch(`http://app-backend-1:8000/auth/check-access/${email}`, { cache: 'no-store' });
        const data = await res.json();
        return data.authorized === true;
      } catch (e) { return false; }
    },
    async session({ session }) {
      // 🛡️ CONTINUOUS VERIFICATION: Check whitelist on EVERY session request
      if (!session.user?.email) return session;
      const email = session.user.email.toLowerCase();
      if (email === "kuljeetsandhu108@gmail.com") return session;
      
      try {
        const res = await fetch(`http://app-backend-1:8000/auth/check-access/${email}`, { cache: 'no-store' });
        const data = await res.json();
        if (!data.authorized) return null; // Kills the session immediately
      } catch (e) { return null; }
      
      return session;
    }
  },
  pages: { error: '/' },
  secret: process.env.NEXTAUTH_SECRET,
});
export { handler as GET, handler as POST };
