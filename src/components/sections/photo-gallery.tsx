"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";
import type { Photo } from "@/types";
import { cn } from "@/lib/utils";

/** Project photo grid with a lightbox and arrow-key navigation. */
export function PhotoGallery({
  photos,
  locale,
  className,
}: {
  photos: Photo[];
  locale: Locale;
  className?: string;
}) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  useEffect(() => {
    if (openIndex === null) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpenIndex(null);
      if (event.key === "ArrowRight") setOpenIndex((i) => (i === null ? i : (i + 1) % photos.length));
      if (event.key === "ArrowLeft")
        setOpenIndex((i) => (i === null ? i : (i - 1 + photos.length) % photos.length));
    };

    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [openIndex, photos.length]);

  if (photos.length === 0) return null;
  const active = openIndex === null ? null : photos[openIndex];

  return (
    <>
      <ul className={cn("grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3", className)}>
        {photos.map((photo, index) => (
          <li key={photo.src}>
            <button
              type="button"
              onClick={() => setOpenIndex(index)}
              className="group relative block aspect-[4/3] w-full overflow-hidden rounded-card border border-line transition-colors hover:border-line-strong"
            >
              <Image
                src={photo.src}
                alt={t(photo.alt, locale)}
                fill
                loading={index < 4 ? "eager" : "lazy"}
                sizes="(min-width: 1024px) 400px, 50vw"
                className="object-cover transition-transform duration-700 ease-[var(--ease-out-expo)] group-hover:scale-105"
              />
            </button>
          </li>
        ))}
      </ul>

      {active ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={t(active.alt, locale)}
          onClick={() => setOpenIndex(null)}
          className="fixed inset-0 z-100 flex items-center justify-center bg-ink-950/95 p-4 sm:p-8"
        >
          <div className="relative w-full max-w-6xl" onClick={(event) => event.stopPropagation()}>
            <div className="relative aspect-[3/2] w-full overflow-hidden rounded-card border border-line">
              <Image
                src={active.src}
                alt={t(active.alt, locale)}
                fill
                sizes="(min-width: 1024px) 1100px, 100vw"
                className="object-contain"
              />
            </div>
            <div className="mt-4 flex items-start justify-between gap-6">
              <p className="text-[14px] text-chalk-400">{t(active.alt, locale)}</p>
              <button
                type="button"
                autoFocus
                onClick={() => setOpenIndex(null)}
                className="rounded-button border border-line px-5 py-2.5 text-[11px] font-medium tracking-[0.16em] text-chalk-200 uppercase transition-colors hover:border-accent hover:text-accent"
              >
                {t(ui.actions.close, locale)}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
