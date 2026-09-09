import type { ElementType, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionProps {
  id?: string;
  as?: ElementType;
  /** `raised` lifts the band one step out of the page background. */
  tone?: "base" | "raised";
  className?: string;
  children: ReactNode;
  "aria-labelledby"?: string;
}

export function Section({
  id,
  as: Tag = "section",
  tone = "base",
  className,
  children,
  ...rest
}: SectionProps) {
  return (
    <Tag
      id={id}
      className={cn(
        "relative py-20 sm:py-24 lg:py-32",
        tone === "raised" && "bg-carbon-900",
        className,
      )}
      {...rest}
    >
      <div className="shell">{children}</div>
    </Tag>
  );
}
