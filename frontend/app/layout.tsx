import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AI Construction Commander",
  description: "Multi-agent root cause analysis for construction projects",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 bg-gray-900">
          <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-8">
            <Link href="/" className="text-orange-400 font-bold text-lg tracking-tight">
              ⚡ AI Construction Commander
            </Link>
            <Link href="/" className="text-sm text-gray-400 hover:text-white transition-colors">Dashboard</Link>
            <Link href="/agent" className="text-sm text-gray-400 hover:text-white transition-colors">Agent</Link>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
