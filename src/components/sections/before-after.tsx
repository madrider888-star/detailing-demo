"use client";

import Image from "next/image";
import { useCallback, useId, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface BeforeAfterProps {
  before: string;
  after: string;
  beforeLabel?: string;
  afterLabel?: string;
  /** Accessible description of what the comparison shows. */
  caption: string;
  className?: string;
  priority?: boolean;
}

/**
 * Drag-to-compare slider. The handle is a real range-style control: it can be
 * dragged with a pointer or moved with the arrow keys when focused.
 */
export function BeforeAfter({
  before,
  after,
  beforeLabel = "Before",
  afterLabel = "After",
  caption,
  className,
  priority = false,
}: BeforeAfterProps) {
  const [position, setPosition] = useState(50);
  const frameRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const labelId = useId();

  const updateFromClientX = useCallback((clientX: number) => {
    const frame = frameRef.current;
    if (!frame) return;
    const rect = frame.getBoundingClientRect();
    const next = ((clientX - rect.left) / rect.width) * 100;
    setPosition(Math.min(100, Math.max(0, next)));
  }, []);

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
    updateFromClientX(event.clientX);
  };

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    updateFromClientX(event.clientX);
  };

  const endDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = false;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    const step = event.shiftKey ? 10 : 2;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      setPosition((value) => Math.max(0, value - step));
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      setPosition((value) => Math.min(100, value + step));
    } else if (event.key === "Home") {
      event.preventDefault();
      setPosition(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setPosition(100);
    }
  };

  return (
    <div
      ref={frameRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      className={cn(
        "group relative aspect-[16/10] w-full cursor-ew-resize overflow-hidden rounded-2xl border border-white/8 select-none",
        className,
      )}
    >
      <span id={labelId} className="sr-only">
        {caption}
      </span>

      <Image
        src={after}
        alt={`${caption} — after`}
        fill
        priority={priority}
        sizes="(min-width: 1024px) 760px, 100vw"
        className="object-cover"
        draggable={false}
      />

      <div
        className="absolute inset-0 overflow-hidden"
        style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
      >
        <Image
          src={before}
          alt={`${caption} — before`}
          fill
          priority={priority}
          sizes="(min-width: 1024px) 760px, 100vw"
          className="object-cover"
          draggable={false}
        />
      </div>

      <span className="glass pointer-events-none absolute top-4 left-4 rounded-full px-3 py-1.5 text-[11px] font-medium tracking-[0.16em] text-mist-200 uppercase">
        {beforeLabel}
      </span>
      <span className="glass pointer-events-none absolute top-4 right-4 rounded-full px-3 py-1.5 text-[11px] font-medium tracking-[0.16em] text-brass-400 uppercase">
        {afterLabel}
      </span>

      <div
        role="slider"
        tabIndex={0}
        aria-labelledby={labelId}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(position)}
        aria-valuetext={`${Math.round(position)}% before`}
        onKeyDown={onKeyDown}
        className="absolute inset-y-0 z-10 -ml-5 w-10 cursor-ew-resize"
        style={{ left: `${position}%` }}
      >
        <span aria-hidden="true" className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-white/70" />
        <span
          aria-hidden="true"
          className="glass absolute top-1/2 left-1/2 grid h-11 w-11 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-white/25 text-mist-100 transition-transform duration-300 group-hover:scale-105"
        >
          <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4">
            <path
              d="M7.5 5 3.5 10l4 5M12.5 5l4 5-4 5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </div>
    </div>
  );
}
