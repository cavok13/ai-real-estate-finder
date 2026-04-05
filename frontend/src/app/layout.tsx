import "./globals.css";
import { ReactNode } from "react";
import { RootProviders } from "./providers";
import { ClientNavRight } from "./nav-right";

export const metadata = {
  title: "AI Deals Finder – Analyze Real Estate with AI",
  description:
    "Paste a property link and get instant ROI, risk analysis, and investor-grade AI summary. Built for real estate investors.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-50 antialiased">
        <RootProviders>
          <div className="min-h-screen flex flex-col">
            <header className="border-b border-slate-800 sticky top-0 z-50 bg-slate-950/90 backdrop-blur-sm">
              <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
                <a href="/" className="font-bold text-lg tracking-tight">
                  <span className="text-emerald-400">AI</span> Deals Finder
                </a>
                <ClientNavRight />
              </div>
            </header>
            <main className="flex-1">{children}</main>
            <footer className="border-t border-slate-800 text-xs text-slate-600">
              <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row justify-between gap-2">
                <span>© {new Date().getFullYear()} AI Deals Finder. All rights reserved.</span>
                <span>Real estate investing powered by AI.</span>
              </div>
            </footer>
          </div>
        </RootProviders>
      </body>
    </html>
  );
}
