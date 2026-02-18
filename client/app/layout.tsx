"use client";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "next-auth/react";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className + " bg-slate-950 text-white antialiased"}>
        <SessionProvider>
          {children}
        </SessionProvider>
      </body>
    </html>
  );
}
