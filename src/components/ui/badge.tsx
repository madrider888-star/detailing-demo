import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface BadgeProps {
  children: ReactNode;
  tone?: "neutral" | "accent";
  className?: string;
}

export function Badge({ children, tone = "neutral", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-[11px] font-medium tracking-[0.14em] uppercase",
        tone === "accent"
          ? "bg-brass-500/12 text-brass-400 ring-1 ring-brass-500/25 ring-inset"
          : "bg-white/[0.05] text-mist-300 ring-1 ring-white/10 ring-inset",
        className,
      )}
    >
      {children}
    </span>
  );
}
