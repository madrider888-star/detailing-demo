"use client";

import { useMemo, useState } from "react";
import { ProjectCard } from "@/components/cards/project-card";
import { services } from "@/content/services";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";
import type { Project } from "@/types";
import { cn } from "@/lib/utils";

/**
 * Portfolio index. Filters are derived from the services each project actually
 * used, so the control list never shows an empty category.
 */
export function PortfolioGrid({
  projects,
  locale,
  className,
}: {
  projects: Project[];
  locale: Locale;
  className?: string;
}) {
  const [filter, setFilter] = useState<string>("all");

  const filters = useMemo(() => {
    const used = new Set(projects.flatMap((project) => project.serviceSlugs));
    return services
      .filter((service) => used.has(service.slug))
      .map((service) => ({ slug: service.slug, label: t(service.title, locale) }));
  }, [projects, locale]);

  const visible = useMemo(
    () =>
      filter === "all"
        ? projects
        : projects.filter((project) => project.serviceSlugs.includes(filter)),
    [filter, projects],
  );

  if (projects.length === 0) {
    return <p className={cn("text-chalk-400", className)}>{t(ui.empty.projects, locale)}</p>;
  }

  return (
    <div className={className}>
      {filters.length > 1 ? (
        <div className="flex flex-wrap gap-2" role="group" aria-label={t(ui.nav.services, locale)}>
          {[{ slug: "all", label: t(ui.labels.filterAll, locale) }, ...filters].map((option) => {
            const selected = filter === option.slug;
            return (
              <button
                key={option.slug}
                type="button"
                aria-pressed={selected}
                onClick={() => setFilter(option.slug)}
                className={cn(
                  "rounded-button border px-4 py-2 text-[11px] font-medium tracking-[0.14em] uppercase transition-colors duration-300",
                  selected
                    ? "border-accent bg-accent/10 text-accent"
                    : "border-line text-chalk-400 hover:border-line-strong hover:text-chalk-50",
                )}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      ) : null}

      <ul className="mt-10 grid grid-flow-row-dense grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((project, index) => (
          <li key={project.slug}>
            <ProjectCard project={project} locale={locale} priority={index < 3} />
          </li>
        ))}
      </ul>
    </div>
  );
}
