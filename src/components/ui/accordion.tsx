"use client";

import { useState } from "react";
import type { Locale } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import type { FaqItem } from "@/types";
import { cn } from "@/lib/utils";

export function Accordion({
  items,
  locale,
  defaultOpen = 0,
  className,
}: {
  items: FaqItem[];
  locale: Locale;
  /** Index opened on first render; pass -1 for an all-closed list. */
  defaultOpen?: number;
  className?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={cn("divide-y divide-line border-y border-line", className)}>
      {items.map((item, index) => {
        const expanded = open === index;
        const question = t(item.question, locale);

        return (
          <div key={question}>
            <h3>
              <button
                type="button"
                onClick={() => setOpen(expanded ? -1 : index)}
                aria-expanded={expanded}
                aria-controls={`faq-panel-${index}`}
                id={`faq-trigger-${index}`}
                className="group flex w-full items-start justify-between gap-6 py-6 text-left"
              >
                <span
                  className={cn(
                    "font-display text-[17px] leading-snug font-medium transition-colors sm:text-xl",
                    expanded ? "text-accent" : "text-chalk-100 group-hover:text-accent",
                  )}
                >
                  {question}
                </span>
                <span
                  aria-hidden="true"
                  className={cn(
                    "relative mt-1 grid h-7 w-7 shrink-0 place-items-center border transition-colors",
                    expanded ? "border-accent text-accent" : "border-line text-chalk-400",
                  )}
                >
                  <span className="absolute h-px w-3 bg-current" />
                  <span
                    className={cn(
                      "absolute h-3 w-px bg-current transition-transform duration-300",
                      expanded && "scale-y-0",
                    )}
                  />
                </span>
              </button>
            </h3>
            <div
              id={`faq-panel-${index}`}
              role="region"
              aria-labelledby={`faq-trigger-${index}`}
              hidden={!expanded}
            >
              <p className="max-w-3xl pr-10 pb-7 text-[15px] leading-relaxed text-chalk-400">
                {t(item.answer, locale)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
