import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrustChain — Multi-Agent Research Team",
  description: "Trust-gated multi-agent research with cryptographic audit trail",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">TC</span>
                </div>
                <h1 className="text-xl font-semibold text-gray-900">TrustChain</h1>
              </div>
              <nav className="flex gap-4">
                <a href="/" className="text-sm font-medium text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md hover:bg-gray-100">
                  Research
                </a>
                <a href="/audit" className="text-sm font-medium text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md hover:bg-gray-100">
                  Audit Trail
                </a>
              </nav>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
