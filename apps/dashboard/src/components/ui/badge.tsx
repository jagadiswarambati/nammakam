import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "safe" | "unsafe" | "escalated" | "pending" | "outline";
}

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-slate-900 text-slate-50 border-transparent",
    safe: "bg-emerald-50 text-emerald-800 border-emerald-300 font-medium",
    unsafe: "bg-rose-50 text-rose-800 border-rose-300 font-medium",
    escalated: "bg-amber-50 text-amber-800 border-amber-300 font-medium",
    pending: "bg-slate-100 text-slate-600 border-slate-300 font-medium",
    outline: "text-slate-950 border-slate-200",
  }[variant];

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
        variantStyles,
        className
      )}
      {...props}
    />
  );
}
