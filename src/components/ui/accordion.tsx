"use client";

import { useState } from "react";
import type { FaqItem } from "@/types";
import { cn } from "@/lib/utils";

interface AccordionProps {
  items: FaqItem[];
  /** Index opened on first render; pass -1 for an all-closed list. */
  defaultOpen?: number;
  className?: string;
}

export function Accordion({ items, defaultOpen = 0, className }: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={cn("divide-y divide-white/8 border-y border-white/8", className)}>
      {items.map((item, index) => {
        const expanded = open === index;
        return (
          <div key={item.question}>
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
                    "font-display text-[17px] leading-snug font-medium transition-colors sm:text-lg",
                    expanded ? "text-mist-100" : "text-mist-200 group-hover:text-mist-100",
                  )}
                >
                  {item.question}
                </span>
                <span
                  aria-hidden="true"
                  className={cn(
                    "relative mt-1 grid h-7 w-7 shrink-0 place-items-center rounded-full border transition-colors",
                    expanded
                      ? "border-brass-500/40 text-brass-400"
                      : "border-white/12 text-mist-400 group-hover:border-white/25",
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
              <p className="max-w-3xl pr-10 pb-7 text-[15px] leading-relaxed text-mist-400">
                {item.answer}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
