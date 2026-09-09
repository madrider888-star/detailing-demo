import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "accent";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-button px-2.5 py-1 text-[10px] font-medium tracking-[0.18em] uppercase",
        tone === "accent"
          ? "bg-accent/12 text-accent ring-1 ring-accent/30 ring-inset"
          : "bg-chalk-50/6 text-chalk-300 ring-1 ring-line ring-inset",
        className,
      )}
    >
      {children}
    </span>
  );
}
