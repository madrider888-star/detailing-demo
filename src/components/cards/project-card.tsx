import Image from "next/image";
import Link from "next/link";
import { services } from "@/content/services";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { Project } from "@/types";
import { cn } from "@/lib/utils";

/**
 * Portfolio tile. The vehicle sits above the project title so the grid scans as
 * a list of cars, which is how visitors arriving from Instagram read it.
 */
export function ProjectCard({
  project,
  locale,
  priority = false,
  size = "default",
  className,
}: {
  project: Project;
  locale: Locale;
  priority?: boolean;
  size?: "default" | "wide";
  className?: string;
}) {
  const performed = project.serviceSlugs
    .map((slug) => services.find((service) => service.slug === slug))
    .filter((service) => service !== undefined)
    .map((service) => t(service.title, locale));

  return (
    <article className={cn("group relative", className)}>
      <Link
        href={localePath(`/portfolio/${project.slug}`, locale)}
        className="block overflow-hidden rounded-card border border-line bg-ink-850 transition-colors duration-500 hover:border-line-strong"
      >
        <div
          className={cn(
            "relative overflow-hidden",
            size === "wide" ? "aspect-[16/9]" : "aspect-[4/5] sm:aspect-[4/3]",
          )}
        >
          {project.cover ? (
            <Image
              src={project.cover.src}
              alt={t(project.cover.alt, locale)}
              fill
              priority={priority}
              sizes={
                size === "wide"
                  ? "(min-width: 1024px) 1200px, 100vw"
                  : "(min-width: 1024px) 460px, (min-width: 640px) 50vw, 100vw"
              }
              className="object-cover transition-transform duration-700 ease-[var(--ease-out-expo)] group-hover:scale-105"
            />
          ) : (
            <div className="absolute inset-0 bg-ink-800" />
          )}
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-gradient-to-t from-ink-950/95 via-ink-950/20 to-transparent"
          />

          <div className="absolute inset-x-0 bottom-0 p-5 sm:p-6">
            <p className="text-[10px] font-medium tracking-[0.22em] text-accent uppercase">
              {project.vehicle}
            </p>
            <h3 className="mt-2 font-display text-xl font-semibold uppercase text-chalk-50 sm:text-2xl">
              {t(project.title, locale)}
            </h3>
            {performed.length > 0 ? (
              <p className="mt-2 text-[13px] text-chalk-400">{performed.join(" · ")}</p>
            ) : null}
          </div>
        </div>
      </Link>
    </article>
  );
}
