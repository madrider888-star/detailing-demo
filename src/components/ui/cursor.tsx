"use client";

import { useEffect, useRef } from "react";

const INTERACTIVE = "a, button, [role='button'], input, select, textarea, label, summary";

/**
 * Lagging pointer ring. Mounted only for mouse-like pointers and only when the
 * visitor has not asked for reduced motion; on touch devices it renders
 * nothing. The native cursor is left untouched — the ring is decoration, not
 * a replacement.
 */
export function Cursor() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const fine = window.matchMedia("(pointer: fine)");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (!fine.matches || reduced.matches) return;

    let targetX = 0;
    let targetY = 0;
    let x = 0;
    let y = 0;
    let frame = 0;
    let visible = false;

    const tick = () => {
      x += (targetX - x) * 0.18;
      y += (targetY - y) * 0.18;
      node.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      frame = requestAnimationFrame(tick);
    };

    const onMove = (event: PointerEvent) => {
      if (event.pointerType !== "mouse") return;
      targetX = event.clientX;
      targetY = event.clientY;
      if (!visible) {
        visible = true;
        x = targetX;
        y = targetY;
        node.dataset.visible = "true";
        frame = requestAnimationFrame(tick);
      }
      const active = (event.target as Element | null)?.closest(INTERACTIVE);
      node.dataset.active = active ? "true" : "false";
    };
    const onLeave = () => {
      node.dataset.visible = "false";
    };
    const onEnter = () => {
      if (visible) node.dataset.visible = "true";
    };
    const onDown = () => {
      node.dataset.pressed = "true";
    };
    const onUp = () => {
      node.dataset.pressed = "false";
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerdown", onDown, { passive: true });
    window.addEventListener("pointerup", onUp, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeave);
    document.documentElement.addEventListener("mouseenter", onEnter);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointerup", onUp);
      document.documentElement.removeEventListener("mouseleave", onLeave);
      document.documentElement.removeEventListener("mouseenter", onEnter);
    };
  }, []);

  return <div ref={ref} aria-hidden="true" className="cursor-ring" />;
}
