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
        return data.authorized === true || data.authorized === "true";
      } catch (e) { return false; }
    }
  },
  pages: { error: '/' },
  secret: process.env.NEXTAUTH_SECRET,
});
export { handler as GET, handler as POST };
