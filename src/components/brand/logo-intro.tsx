"use client";

import { useEffect, useRef, useState } from "react";
import { LOGO_LETTERS, LOGO_VIEWBOX } from "@/components/brand/logo-paths";

const SEEN_KEY = "thebox-intro-seen";
const SAFETY_MS = 4500;

/**
 * Opening sequence, once per browser session: on a black screen the letters of
 * THE BOX are drawn along their outlines, fill in, a polish-like highlight
 * sweeps across them, and the mark glides into its place above the headline
 * (or simply fades away on pages without one). About two seconds, skippable
 * with a tap, never shown to visitors who prefer reduced motion. GSAP is
 * loaded on demand, so returning visitors never download it.
 */
export function LogoIntro() {
  const rootRef = useRef<HTMLDivElement>(null);
  const skipRef = useRef<() => void>(() => {});
  const [done, setDone] = useState(false);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let seen = false;
    try {
      seen = window.sessionStorage.getItem(SEEN_KEY) === "1";
    } catch {
      /* storage unavailable: play once per page load */
    }
    if (reduced || seen) {
      setDone(true);
      return;
    }

    let finished = false;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const target = document.querySelector<HTMLElement>("[data-hero-logo]");
    target?.style.setProperty("opacity", "0");

    const finish = () => {
      if (finished) return;
      finished = true;
      try {
        window.sessionStorage.setItem(SEEN_KEY, "1");
      } catch {
        /* ignore */
      }
      document.body.style.overflow = previousOverflow;
      target?.style.removeProperty("opacity");
      setDone(true);
    };
    const safety = window.setTimeout(finish, SAFETY_MS);

    let timeline: { progress: (value: number) => unknown; kill: () => void } | null = null;
    skipRef.current = () => {
      if (timeline) timeline.progress(1);
      else finish();
    };

    (async () => {
      const { gsap } = await import("gsap");
      if (finished) return;

      const svg = root.querySelector<SVGSVGElement>("svg");
      const gloss = root.querySelector<SVGRectElement>("[data-gloss]");
      if (!svg || !gloss) return finish();
      // pathLength="1" normalises every outline, so the server-rendered
      // markup already starts with the stroke fully hidden (dashoffset 1).
      const letters = Array.from(svg.querySelectorAll<SVGPathElement>("path[data-letter]"));

      const tl = gsap.timeline({ defaults: { ease: "power2.inOut" }, onComplete: finish });
      timeline = tl;

      // 1. Outlines draw themselves, letter after letter.
      tl.to(letters, { strokeDashoffset: 0, duration: 0.8, stagger: 0.05 })
        // 2. The letters fill while the last outlines are still closing.
        .to(letters, { fillOpacity: 1, duration: 0.4, stagger: 0.04 }, "-=0.45")
        // 3. A highlight passes over the mark, like light over fresh polish.
        .fromTo(
          gloss,
          { attr: { x: -1200 } },
          { attr: { x: 3000 }, duration: 0.65, ease: "power2.inOut" },
          "-=0.2",
        );

      // 4. Hand-off: glide into the hero's logo slot, or fade out elsewhere.
      if (target) {
        const from = svg.getBoundingClientRect();
        const to = target.getBoundingClientRect();
        const scale = to.width / from.width;
        const dx = to.left + to.width / 2 - (from.left + from.width / 2);
        const dy = to.top + to.height / 2 - (from.top + from.height / 2);
        tl.to(svg, { x: dx, y: dy, scale, duration: 0.6, ease: "expo.inOut" }, "+=0.05").to(
          root,
          { backgroundColor: "rgba(5,5,5,0)", duration: 0.4, ease: "power1.out" },
          "<0.2",
        );
      } else {
        tl.to(svg, { scale: 1.04, opacity: 0, duration: 0.45, ease: "power2.in" }, "+=0.15").to(
          root,
          { opacity: 0, duration: 0.35 },
          "<0.1",
        );
      }
    })().catch(finish);

    return () => {
      window.clearTimeout(safety);
      timeline?.kill();
      finish();
    };
  }, []);

  if (done) return null;

  return (
    <div
      ref={rootRef}
      data-logo-intro=""
      aria-hidden="true"
      onClick={() => skipRef.current()}
      className="fixed inset-0 z-[300] grid place-items-center bg-ink-950 text-chalk-50"
    >
      <svg viewBox={LOGO_VIEWBOX} className="w-[150px] will-change-transform sm:w-[220px]">
        <defs>
          <linearGradient id="logo-intro-gloss" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="0" />
            <stop offset="0.5" stopColor="#fff" stopOpacity="0.55" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
          <clipPath id="logo-intro-clip">
            {LOGO_LETTERS.map((letter) => (
              <path key={letter.id} d={letter.d} />
            ))}
          </clipPath>
        </defs>
        {LOGO_LETTERS.map((letter) => (
          <path
            key={letter.id}
            d={letter.d}
            data-letter={letter.id}
            pathLength={1}
            fill="currentColor"
            fillOpacity={0}
            stroke="currentColor"
            strokeWidth={14}
            strokeLinejoin="round"
            style={{ strokeDasharray: 1, strokeDashoffset: 1 }}
          />
        ))}
        <g clipPath="url(#logo-intro-clip)">
          <rect
            data-gloss=""
            x={-1200}
            y={-400}
            width={700}
            height={2600}
            fill="url(#logo-intro-gloss)"
            transform="skewX(-22)"
          />
        </g>
      </svg>
    </div>
  );
}
