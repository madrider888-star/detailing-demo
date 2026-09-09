"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { galleryFilters } from "@/content/gallery";
import type { GalleryCategory, GalleryItem } from "@/types";
import { cn } from "@/lib/utils";

interface GalleryGridProps {
  items: GalleryItem[];
  className?: string;
}

const categoryLabel: Record<GalleryCategory, string> = {
  "before-after": "Before / After",
  ceramic: "Ceramic Coating",
  ppf: "Paint Protection Film",
  interior: "Interior",
  correction: "Paint Correction",
};

export function GalleryGrid({ items, className }: GalleryGridProps) {
  const [filter, setFilter] = useState<GalleryCategory | "all">("all");
  const [active, setActive] = useState<GalleryItem | null>(null);

  const visible = useMemo(
    () => (filter === "all" ? items : items.filter((item) => item.category === filter)),
    [filter, items],
  );

  useEffect(() => {
    if (!active) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setActive(null);
    };
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [active]);

  return (
    <div className={className}>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter gallery by service">
        {galleryFilters.map((option) => {
          const selected = filter === option.id;
          return (
            <button
              key={option.id}
              type="button"
              aria-pressed={selected}
              onClick={() => setFilter(option.id)}
              className={cn(
                "rounded-full border px-4 py-2 text-[13px] font-medium transition-colors duration-300",
                selected
                  ? "border-brass-500/40 bg-brass-500/10 text-brass-300"
                  : "border-white/10 text-mist-400 hover:border-white/22 hover:text-mist-100",
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>

      {/* Wide tiles claim a whole row; dense flow backfills the gap they leave. */}
      <ul className="mt-10 grid grid-flow-row-dense grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((item, index) => (
          <li key={item.id} className={cn(item.span === "wide" && "sm:col-span-2 lg:col-span-3")}>
            <button
              type="button"
              onClick={() => setActive(item)}
              className="group relative block w-full overflow-hidden rounded-2xl border border-white/8 bg-carbon-850 text-left transition-[border-color] duration-500 hover:border-white/20"
            >
              <span
                className={cn(
                  "relative block",
                  item.span === "wide" ? "aspect-[16/9] sm:aspect-[2.4/1]" : "aspect-[4/3]",
                )}
              >
                <Image
                  src={item.image}
                  alt={`${item.title} — ${item.vehicle}`}
                  fill
                  loading={index < 3 ? "eager" : "lazy"}
                  sizes={
                    item.span === "wide"
                      ? "(min-width: 1024px) 1360px, 100vw"
                      : "(min-width: 1024px) 380px, (min-width: 640px) 50vw, 100vw"
                  }
                  className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
                />
              </span>
              <span
                aria-hidden="true"
                className="absolute inset-0 bg-gradient-to-t from-carbon-950/90 via-carbon-950/10 to-transparent"
              />
              <span className="absolute inset-x-0 bottom-0 flex flex-col gap-1 p-5">
                <span className="text-[11px] font-medium tracking-[0.18em] text-brass-500 uppercase">
                  {categoryLabel[item.category]}
                </span>
                <span className="font-display text-[17px] font-medium text-mist-100">
                  {item.title}
                </span>
                <span className="text-[13px] text-mist-400">{item.vehicle}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>

      {visible.length === 0 ? (
        <p className="mt-10 text-mist-400">No work in this category yet.</p>
      ) : null}

      {active ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`${active.title} — ${active.vehicle}`}
          className="fixed inset-0 z-100 flex items-center justify-center bg-carbon-950/92 p-4 backdrop-blur-sm sm:p-8"
          onClick={() => setActive(null)}
        >
          <div
            className="relative w-full max-w-5xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="relative aspect-[3/2] w-full overflow-hidden rounded-2xl border border-white/10">
              <Image
                src={active.image}
                alt={`${active.title} — ${active.vehicle}`}
                fill
                sizes="(min-width: 1024px) 960px, 100vw"
                className="object-cover"
              />
            </div>
            <div className="mt-5 flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-medium tracking-[0.18em] text-brass-500 uppercase">
                  {categoryLabel[active.category]}
                </p>
                <h3 className="mt-2 font-display text-xl font-medium">{active.title}</h3>
                <p className="mt-1 text-[14px] text-mist-400">{active.vehicle}</p>
              </div>
              <button
                type="button"
                autoFocus
                onClick={() => setActive(null)}
                className="rounded-full border border-white/12 px-5 py-2.5 text-[13px] font-medium text-mist-200 transition-colors hover:border-white/25 hover:text-mist-100"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
