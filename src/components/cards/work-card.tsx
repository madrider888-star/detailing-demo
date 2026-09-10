import Image from "next/image";
import Link from "next/link";
import { ArrowIcon } from "@/components/ui/button";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { WorkProject } from "@/types";
import { cn } from "@/lib/utils";

const PREVIEW_ITEMS = 3;

/**
 * Tile in "Our work": cover, vehicle, the first few confirmed jobs and a link.
 * The whole card is clickable through the title link.
 */
export function WorkCard({
  project,
  locale,
  priority = false,
  className,
}: {
  project: WorkProject;
  locale: Locale;
  priority?: boolean;
  className?: string;
}) {
  if (!project.cover) return null;

  const href = localePath(`/portfolio/${project.slug}`, locale);
  const preview = project.works.slice(0, PREVIEW_ITEMS);
  const rest = project.works.length - preview.length;
  const hasVideo = project.videos.length > 0;

  return (
    <article
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-card border border-line bg-ink-850",
        "transition-[border-color,transform] duration-500 ease-[var(--ease-out-expo)] hover:-translate-y-1 hover:border-line-strong",
        className,
      )}
    >
      <div className="relative aspect-[4/5] overflow-hidden">
        <Image
          src={project.cover.src}
          alt={`${project.vehicle} — THE BOX Detailing`}
          fill
          priority={priority}
          sizes="(min-width: 1024px) 420px, (min-width: 640px) 50vw, 100vw"
          className="object-cover transition-transform duration-700 ease-[var(--ease-out-expo)] group-hover:scale-105"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-gradient-to-t from-ink-850 via-transparent to-transparent"
        />
        {hasVideo ? (
          <span className="glass absolute top-3 right-3 inline-flex items-center gap-1.5 rounded-button px-2.5 py-1 text-[10px] font-medium tracking-[0.18em] text-chalk-100 uppercase">
            <svg viewBox="0 0 16 16" aria-hidden="true" className="h-3 w-3 fill-current">
              <path d="M4 2.5v11l9-5.5-9-5.5Z" />
            </svg>
            {t(ui.work.video, locale)}
          </span>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col p-5 sm:p-6">
        <h3 className="font-display text-xl font-semibold uppercase leading-tight sm:text-2xl">
          <Link href={href} className="before:absolute before:inset-0">
            {project.vehicle}
          </Link>
        </h3>

        <ul className="mt-4 space-y-1.5 text-[13.5px] leading-snug text-chalk-400">
          {preview.map((item) => (
            <li key={item.en} className="flex gap-2">
              <span aria-hidden="true" className="mt-[9px] h-px w-3 shrink-0 bg-accent-muted" />
              <span className="line-clamp-2">{item[locale]}</span>
            </li>
          ))}
          {rest > 0 ? <li className="pl-5 text-chalk-500">+{rest}</li> : null}
        </ul>

        <span className="mt-auto inline-flex items-center gap-2 pt-6 text-[11px] font-medium tracking-[0.16em] text-chalk-200 uppercase transition-colors group-hover:text-accent">
          {t(ui.work.viewProject, locale)}
          <ArrowIcon className="transition-transform duration-300 group-hover:translate-x-1" />
        </span>
      </div>
    </article>
  );
}
