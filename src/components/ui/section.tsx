import type { ElementType, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionProps {
  id?: string;
  as?: ElementType;
  /** `raised` lifts the band one step out of the page background. */
  tone?: "base" | "raised";
  /** `flush` drops the shell gutter for full-bleed media. */
  bleed?: boolean;
  className?: string;
  children: ReactNode;
  "aria-labelledby"?: string;
}

export function Section({
  id,
  as: Tag = "section",
  tone = "base",
  bleed = false,
  className,
  children,
  ...rest
}: SectionProps) {
  return (
    <Tag
      id={id}
      className={cn("relative py-20 sm:py-28 lg:py-36", tone === "raised" && "bg-ink-900", className)}
      {...rest}
    >
      {bleed ? children : <div className="shell">{children}</div>}
    </Tag>
  );
}
