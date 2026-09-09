"use client";

import { useEffect, useRef, useState } from "react";
import type { ElementType, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface RevealProps {
  children: ReactNode;
  /** Stagger in milliseconds, applied as an animation delay. */
  delay?: number;
  as?: ElementType;
  className?: string;
}

/**
 * Fades content up the first time it enters the viewport.
 *
 * Content is rendered server-side either way; the `data-reveal` hook lets the
 * no-script stylesheet in the root layout force it visible when JS is off.
 */
export function Reveal({ children, delay = 0, as: Tag = "div", className }: RevealProps) {
  const ref = useRef<HTMLElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setShown(true);
            observer.disconnect();
          }
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      data-reveal=""
      style={shown && delay ? { animationDelay: `${delay}ms` } : undefined}
      className={cn(shown ? "animate-rise" : "opacity-0", className)}
    >
      {children}
    </Tag>
  );
}
