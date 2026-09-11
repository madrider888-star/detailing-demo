"use client";

import { useRef, type PointerEvent, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Pulls its child a few pixels toward the mouse while the pointer hovers
 * nearby, and eases it back on leave. Touch pointers are ignored, so on a
 * phone this is an ordinary wrapper.
 */
export function Magnetic({
  children,
  strength = 0.35,
  className,
}: {
  children: ReactNode;
  /** How far the child follows the pointer: 0 = not at all, 1 = fully. */
  strength?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  const onMove = (event: PointerEvent<HTMLSpanElement>) => {
    const node = ref.current;
    if (!node || event.pointerType !== "mouse") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const rect = node.getBoundingClientRect();
    const dx = event.clientX - (rect.left + rect.width / 2);
    const dy = event.clientY - (rect.top + rect.height / 2);
    node.style.transition = "transform 0.15s ease-out";
    node.style.transform = `translate3d(${(dx * strength).toFixed(1)}px, ${(dy * strength).toFixed(1)}px, 0)`;
  };

  const onLeave = () => {
    const node = ref.current;
    if (!node) return;
    node.style.transition = "transform 0.6s var(--ease-out-expo)";
    node.style.transform = "translate3d(0, 0, 0)";
  };

  return (
    <span
      ref={ref}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      className={cn("inline-flex will-change-transform", className)}
    >
      {children}
    </span>
  );
}
