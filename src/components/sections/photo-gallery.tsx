"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";
import type { Photo } from "@/types";
import { cn } from "@/lib/utils";

const SWIPE_PX = 48;

/**
 * Project photo grid with a full-screen lightbox: swipe or arrow keys to move
 * between frames, a counter, a thumbnail strip on wide screens, and a tap on
 * the picture to zoom into the detail. Tiles keep the photographs' own
 * proportions when they are known.
 */
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
  const [zoomed, setZoomed] = useState(false);
  const [origin, setOrigin] = useState("50% 50%");
  const swipeStart = useRef<{ x: number; y: number } | null>(null);
  const swipedAt = useRef(0);
  const stripRef = useRef<HTMLUListElement>(null);

  const count = photos.length;
  const go = useCallback(
    (delta: number) => {
      setZoomed(false);
      setOpenIndex((i) => (i === null ? i : (i + delta + count) % count));
    },
    [count],
  );
  const close = useCallback(() => {
    setZoomed(false);
    setOpenIndex(null);
  }, []);

  useEffect(() => {
    if (openIndex === null) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
      if (event.key === "ArrowRight") go(1);
      if (event.key === "ArrowLeft") go(-1);
    };

    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [openIndex, go, close]);

  // Keep the active thumbnail in view.
  useEffect(() => {
    if (openIndex === null) return;
    const strip = stripRef.current;
    const item = strip?.children[openIndex] as HTMLElement | undefined;
    item?.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
  }, [openIndex]);

  if (count === 0) return null;
  const active = openIndex === null ? null : photos[openIndex];

  const portraitMajority = photos.filter((p) => p.width && p.height && p.height > p.width).length > count / 2;

  const onPointerDown = (event: ReactPointerEvent) => {
    if (zoomed) return;
    swipeStart.current = { x: event.clientX, y: event.clientY };
  };
  const onPointerUp = (event: ReactPointerEvent) => {
    const start = swipeStart.current;
    swipeStart.current = null;
    if (!start || zoomed) return;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (Math.abs(dx) > SWIPE_PX && Math.abs(dx) > Math.abs(dy) * 1.5) {
      swipedAt.current = Date.now();
      go(dx < 0 ? 1 : -1);
    }
  };
  const toggleZoom = (event: ReactPointerEvent<HTMLButtonElement>) => {
    // A swipe ends with a click on the same button; that click must not zoom.
    if (Date.now() - swipedAt.current < 400) return;
    const rect = event.currentTarget.getBoundingClientRect();
    setOrigin(`${(((event.clientX - rect.left) / rect.width) * 100).toFixed(1)}% ${(((event.clientY - rect.top) / rect.height) * 100).toFixed(1)}%`);
    setZoomed((z) => !z);
  };

  return (
    <>
      <ul className={cn("grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3", className)}>
        {photos.map((photo, index) => (
          <li key={photo.src}>
            <button
              type="button"
              onClick={() => setOpenIndex(index)}
              aria-label={t(photo.alt, locale)}
              className={cn(
                "group relative block w-full overflow-hidden rounded-card border border-line transition-colors hover:border-line-strong",
                portraitMajority ? "aspect-[4/5]" : "aspect-[4/3]",
              )}
            >
              <Image
                src={photo.src}
                alt={t(photo.alt, locale)}
                fill
                loading={index < 4 ? "eager" : "lazy"}
                placeholder={photo.blur ? "blur" : "empty"}
                blurDataURL={photo.blur}
                sizes="(min-width: 1024px) 400px, 50vw"
                className="object-cover transition-transform duration-700 ease-[var(--ease-out-expo)] group-hover:scale-105"
              />
            </button>
          </li>
        ))}
      </ul>

      {active && openIndex !== null ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={t(active.alt, locale)}
          className="fixed inset-0 z-100 flex flex-col bg-ink-950/97 backdrop-blur-sm"
        >
          <div className="shell flex h-14 shrink-0 items-center justify-between sm:h-16">
            <p className="font-display text-[13px] tracking-[0.2em] text-chalk-300 tabular-nums">
              {openIndex + 1} <span className="text-chalk-500">/ {count}</span>
            </p>
            <button
              type="button"
              autoFocus
              onClick={close}
              className="-mr-2 inline-flex h-11 items-center gap-2 px-2 text-[11px] font-medium tracking-[0.16em] text-chalk-200 uppercase transition-colors hover:text-accent"
            >
              {t(ui.actions.close, locale)}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-5 w-5">
                <path d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </div>

          <div
            className="relative flex min-h-0 flex-1 touch-pan-y select-none items-center justify-center"
            onPointerDown={onPointerDown}
            onPointerUp={onPointerUp}
            onPointerCancel={() => (swipeStart.current = null)}
          >
            <button
              type="button"
              onClick={toggleZoom}
              aria-label={zoomed ? t(ui.gallery.zoomOut, locale) : t(ui.gallery.zoomIn, locale)}
              className={cn(
                "relative block h-full w-full overflow-hidden",
                zoomed ? "cursor-zoom-out" : "cursor-zoom-in",
              )}
            >
              <Image
                key={active.src}
                src={active.src}
                alt={t(active.alt, locale)}
                fill
                priority
                placeholder={active.blur ? "blur" : "empty"}
                blurDataURL={active.blur}
                sizes="100vw"
                draggable={false}
                style={{ transformOrigin: origin }}
                className={cn(
                  "object-contain transition-transform duration-500 ease-[var(--ease-out-expo)]",
                  zoomed ? "scale-[2.2]" : "scale-100",
                )}
              />
            </button>

            {/* Neighbours are fetched quietly so the next swipe is instant. */}
            {[openIndex - 1, openIndex + 1].map((i) => {
              const neighbour = photos[(i + count) % count];
              return !neighbour || neighbour.src === active.src ? null : (
                <Image
                  key={neighbour.src}
                  src={neighbour.src}
                  alt=""
                  aria-hidden="true"
                  fill
                  sizes="100vw"
                  className="pointer-events-none object-contain opacity-0"
                />
              );
            })}

            {count > 1 ? (
              <>
                <NavButton side="prev" label={t(ui.gallery.previous, locale)} onClick={() => go(-1)} />
                <NavButton side="next" label={t(ui.gallery.next, locale)} onClick={() => go(1)} />
              </>
            ) : null}
          </div>

          <div className="shell shrink-0 py-3 sm:py-4">
            <p className="truncate text-center text-[13px] text-chalk-400 sm:hidden">{t(active.alt, locale)}</p>
            {count > 1 ? (
              <ul
                ref={stripRef}
                className="hidden justify-center gap-2 overflow-x-auto pb-1 sm:flex [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
              >
                {photos.map((photo, index) => (
                  <li key={photo.src} className="shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        setZoomed(false);
                        setOpenIndex(index);
                      }}
                      aria-label={t(photo.alt, locale)}
                      aria-current={index === openIndex ? "true" : undefined}
                      className={cn(
                        "relative block h-14 w-14 overflow-hidden rounded-card border transition-[opacity,border-color] duration-300",
                        index === openIndex ? "border-accent opacity-100" : "border-transparent opacity-45 hover:opacity-80",
                      )}
                    >
                      <Image src={photo.src} alt="" fill sizes="56px" className="object-cover" />
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      ) : null}
    </>
  );
}

function NavButton({ side, label, onClick }: { side: "prev" | "next"; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className={cn(
        "glass absolute top-1/2 hidden h-12 w-12 -translate-y-1/2 place-items-center rounded-button border border-line text-chalk-100 transition-colors hover:border-accent hover:text-accent sm:grid",
        side === "prev" ? "left-4 lg:left-8" : "right-4 lg:right-8",
      )}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={cn("h-5 w-5", side === "prev" && "rotate-180")}>
        <path d="M4 12h15M13 6l6 6-6 6" />
      </svg>
    </button>
  );
}
