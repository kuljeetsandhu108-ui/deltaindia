import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function middleware(req: NextRequest) {
  const session = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const { pathname } = req.nextUrl;

  // Protect all dashboard routes
  if (pathname.startsWith('/dashboard')) {
    if (!session || !session.email) {
      return NextResponse.redirect(new URL('/', req.url));
    }

    const email = session.email.toLowerCase();
    
    // MASTER ADMIN BYPASS
    if (email === "kuljeetsandhu108@gmail.com") return NextResponse.next();

    // ACTIVE CHECK: Talk to backend to see if this user is still whitelisted
    try {
      const res = await fetch(`http://app-backend-1:8000/auth/check-access/${email}`, { cache: 'no-store' });
      const data = await res.json();
      if (!data.authorized) {
        return NextResponse.redirect(new URL('/', req.url));
      }
    } catch (e) {
      return NextResponse.redirect(new URL('/', req.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
