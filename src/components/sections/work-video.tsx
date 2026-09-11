"use client";

import Image from "next/image";
import { useState } from "react";
import { Icon } from "@/components/ui/icon";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";
import type { WorkVideo } from "@/types";
import { cn } from "@/lib/utils";

/**
 * A reel, loaded only when the visitor asks for it: the poster is a plain
 * image until the play button is pressed, then the <video> element mounts
 * with controls. When the file is not on the site the poster links to the
 * original Instagram post instead.
 */
export function WorkVideoPlayer({
  video,
  vehicle,
  locale,
  className,
}: {
  video: WorkVideo;
  vehicle: string;
  locale: Locale;
  className?: string;
}) {
  const [playing, setPlaying] = useState(false);
  const alt = `${vehicle} — ${t(ui.work.video, locale)}`;

  return (
    <figure
      className={cn(
        "relative aspect-[9/16] w-full overflow-hidden rounded-card border border-line bg-ink-900",
        className,
      )}
    >
      {playing && video.src ? (
        <video
          src={video.src}
          poster={video.poster.src}
          controls
          autoPlay
          playsInline
          preload="none"
          className="h-full w-full object-cover"
        >
          <a href={video.sourceUrl}>{t(ui.work.watchOnInstagram, locale)}</a>
        </video>
      ) : (
        <>
          <Image
            src={video.poster.src}
            alt={alt}
            fill
            placeholder={video.poster.blur ? "blur" : "empty"}
            blurDataURL={video.poster.blur}
            sizes="(min-width: 1024px) 380px, 100vw"
            className="object-cover"
          />
          <div aria-hidden="true" className="absolute inset-0 bg-ink-950/25" />
          {video.src ? (
            <button
              type="button"
              onClick={() => setPlaying(true)}
              aria-label={`${t(ui.work.playVideo, locale)}: ${vehicle}`}
              className="group absolute inset-0 flex items-center justify-center"
            >
              <PlayBadge label={t(ui.work.playVideo, locale)} />
            </button>
          ) : (
            <a
              href={video.sourceUrl}
              target="_blank"
              rel="noreferrer noopener"
              className="group absolute inset-0 flex items-center justify-center"
            >
              <PlayBadge label={t(ui.work.watchOnInstagram, locale)} external />
            </a>
          )}
        </>
      )}
    </figure>
  );
}

function PlayBadge({ label, external = false }: { label: string; external?: boolean }) {
  return (
    <span className="glass inline-flex items-center gap-3 rounded-button border border-line-strong px-4 py-3 text-[11px] font-medium tracking-[0.16em] text-chalk-50 uppercase transition-colors group-hover:border-accent group-hover:text-accent">
      {external ? (
        <Icon name="instagram" className="h-4 w-4" />
      ) : (
        <svg viewBox="0 0 16 16" aria-hidden="true" className="h-3.5 w-3.5 fill-current">
          <path d="M4 2.5v11l9-5.5-9-5.5Z" />
        </svg>
      )}
      {label}
    </span>
  );
}
