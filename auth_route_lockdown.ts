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
      
      // 👑 MASTER ADMIN ALWAYS ALLOWED
      if (email === "kuljeetsandhu108@gmail.com") return true;

      try {
        // Talk to backend via internal Docker network for 100% reliability
        const res = await fetch(`http://app-backend-1:8000/auth/check-access/${email}`, {
            cache: 'no-store'
        });
        const data = await res.json();
        
        if (data.authorized === true) {
            return true;
        } else {
            // 🚫 HARD BLOCK
            return false; 
        }
      } catch (error) {
        // If system is unsure, BLOCK ACCESS for safety
        return false;
      }
    },
  },
  pages: {
    error: '/', 
  },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
