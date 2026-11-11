import Link from "next/link";
import { ShieldCheck, Layers, FileCheck2 } from "lucide-react";

export function Navigation() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white shadow-sm group-hover:bg-indigo-600 transition-colors">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900">
                Nammakam
              </span>
              <span className="ml-2 text-xs font-medium text-slate-500 hidden sm:inline">
                AI Safety Evaluation
              </span>
            </div>
          </Link>
          <nav className="flex items-center gap-1 text-sm font-medium">
            <Link
              href="/"
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              <Layers className="h-4 w-4" />
              <span>Overview</span>
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 border border-slate-200">
            <span className="mr-1.5 h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            FastAPI Connected
          </span>
        </div>
      </div>
    </header>
  );
}

