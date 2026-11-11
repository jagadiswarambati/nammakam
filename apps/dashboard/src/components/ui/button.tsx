import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variantStyles = {
      default:
        "bg-slate-900 text-slate-50 hover:bg-slate-800 shadow active:scale-[0.98]",
      destructive:
        "bg-rose-600 text-white hover:bg-rose-700 shadow-sm active:scale-[0.98]",
      outline:
        "border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 shadow-sm",
      secondary:
        "bg-slate-100 text-slate-900 hover:bg-slate-200",
      ghost: "hover:bg-slate-100 text-slate-700",
    }[variant];

    const sizeStyles = {
      default: "h-9 px-4 py-2 text-sm",
      sm: "h-8 rounded-md px-3 text-xs",
      lg: "h-11 rounded-md px-8 text-base",
      icon: "h-9 w-9 p-0",
    }[size];

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-lg font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          variantStyles,
          sizeStyles,
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
