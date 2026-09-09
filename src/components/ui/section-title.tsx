import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionTitleProps {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  align?: "left" | "center";
  /** Optional element rendered on the opposite side on large screens. */
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
      <div className={cn("max-w-2xl", centered && "mx-auto text-center")}>
        {eyebrow ? (
          <p className={cn("eyebrow", centered && "justify-center")}>
            <span aria-hidden="true" className="h-px w-8 bg-brass-600/70" />
            {eyebrow}
          </p>
        ) : null}
        <h2
          id={id}
          className="mt-5 text-3xl leading-[1.08] font-semibold sm:text-4xl lg:text-[2.75rem]"
        >
          {title}
        </h2>
        {description ? (
          <p className="mt-5 text-base leading-relaxed text-mist-400 sm:text-[17px]">
            {description}
          </p>
        ) : null}
      </div>
      {aside ? <div className="shrink-0">{aside}</div> : null}
    </div>
  );
}
