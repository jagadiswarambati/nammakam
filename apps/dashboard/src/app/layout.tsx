import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Navigation } from "@/components/navigation";

export const metadata: Metadata = {
  title: "Nammakam — AI Safety Evaluation Platform",
  description:
    "Safety evaluation and cross-lingual parity platform for Indian-language banking voice and chat agents.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased flex flex-col">
        <Providers>
          <Navigation />
          <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
          <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
            <p>
              Baseline evaluation of Nammakam’s synthetic mock bank agent. All
              data is synthetic; zero connection to live payment rails.
            </p>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
