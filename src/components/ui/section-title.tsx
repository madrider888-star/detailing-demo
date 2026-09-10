import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionTitleProps {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  align?: "left" | "center";
  /** Rendered opposite the title on large screens — usually a link or button. */
  aside?: ReactNode;
  id?: string;
  className?: string;
}

export function SectionTitle({
  eyebrow,
  title,
  description,
  align = "left",
  aside,
  id,
  className,
}: SectionTitleProps) {
  const centered = align === "center";

  return (
    <div
      className={cn(
        "flex flex-col gap-8",
        Boolean(aside) && "lg:flex-row lg:items-end lg:justify-between lg:gap-16",
        className,
      )}
    >
      <div className={cn("max-w-3xl", centered && "mx-auto text-center")}>
        {eyebrow ? (
          <p className={cn("eyebrow", centered && "justify-center")}>
            <span aria-hidden="true" className="h-px w-8 bg-accent-muted" />
            {eyebrow}
          </p>
        ) : null}
        <h2
          id={id}
          className="mt-6 text-[2rem] font-semibold uppercase sm:text-[2.75rem] lg:text-[3.25rem]"
        >
          {title}
        </h2>
        {description ? (
          <p className="mt-6 text-base leading-relaxed text-chalk-400 sm:text-[17px]">
            {description}
          </p>
        ) : null}
      </div>
      {aside ? <div className="shrink-0">{aside}</div> : null}
    </div>
  );
}
