"use client";

import { useState } from "react";
import { BeforeAfter } from "@/components/sections/before-after";
import type { ComparisonPair } from "@/types";
import { cn } from "@/lib/utils";

export function ComparisonShowcase({ pairs }: { pairs: ComparisonPair[] }) {
  const [activeId, setActiveId] = useState(pairs[0]?.id ?? "");
  const active = pairs.find((pair) => pair.id === activeId) ?? pairs[0];

  if (!active) return null;

  return (
    <div className="grid gap-10 lg:grid-cols-[1.4fr_1fr] lg:items-center lg:gap-16">
      <BeforeAfter
        key={active.id}
        before={active.before}
        after={active.after}
        caption={`${active.title} on a ${active.vehicle}`}
      />

      <div>
        <div role="tablist" aria-label="Before and after case studies" className="flex flex-col">
          {pairs.map((pair) => {
            const selected = pair.id === active.id;
            return (
              <button
                key={pair.id}
                role="tab"
                type="button"
                aria-selected={selected}
                onClick={() => setActiveId(pair.id)}
                className={cn(
                  "group border-t border-white/8 py-5 text-left transition-colors last:border-b",
                  selected ? "text-mist-100" : "text-mist-400 hover:text-mist-200",
                )}
              >
                <span className="flex items-center justify-between gap-4">
                  <span className="font-display text-[17px] font-medium">{pair.title}</span>
                  <span
                    aria-hidden="true"
                    className={cn(
                      "h-1.5 w-1.5 rounded-full transition-colors",
                      selected ? "bg-brass-500" : "bg-carbon-600 group-hover:bg-carbon-500",
                    )}
                  />
                </span>
                <span className="mt-1 block text-[13px] text-mist-500">{pair.vehicle}</span>
              </button>
            );
          })}
        </div>

        <p className="mt-7 text-[15px] leading-relaxed text-mist-400">{active.description}</p>
        <p className="mt-6 text-[12.5px] tracking-[0.14em] text-mist-500 uppercase">
          Drag the handle to compare
        </p>
      </div>
    </div>
  );
}
