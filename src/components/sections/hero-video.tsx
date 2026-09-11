"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import type { HeroVideo as HeroVideoContent } from "@/types";
import { t, type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * Full-bleed background clip for the home page hero.
 *
 * The poster is the LCP image and paints first. The <video> is mounted only
 * after the page is interactive and only when the visitor has not asked for
 * reduced motion or data saving, then fades in once it can actually play.
 * Muted, looping, inline: it behaves like a moving photograph, never a player.
 */
export function HeroVideo({ video, locale }: { video: HeroVideoContent; locale: Locale }) {
  const [wanted, setWanted] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    if (reduced || connection?.saveData) return;
    const id = window.setTimeout(() => setWanted(true), 300);
    return () => window.clearTimeout(id);
  }, []);

  return (
    <>
      <Image
        src={video.poster.src}
        alt={t(video.poster.alt, locale)}
        fill
        priority
        sizes="100vw"
        placeholder={video.poster.blur ? "blur" : "empty"}
        blurDataURL={video.poster.blur}
        className="object-cover object-center"
      />
      {wanted ? (
        <video
          src={video.src}
          poster={video.poster.src}
          muted
          autoPlay
          loop
          playsInline
          preload="auto"
          disablePictureInPicture
          aria-hidden="true"
          tabIndex={-1}
          onPlaying={() => setPlaying(true)}
          className={cn(
            "absolute inset-0 h-full w-full object-cover object-center transition-opacity duration-[1200ms] ease-out",
            playing ? "opacity-100" : "opacity-0",
          )}
        />
      ) : null}
    </>
  );
}
