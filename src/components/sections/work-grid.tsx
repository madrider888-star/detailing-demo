"use client";

import { useMemo, useState } from "react";
import { WorkCard } from "@/components/cards/work-card";
import { Button } from "@/components/ui/button";
import { ui } from "@/content/ui";
import { WORK_PAGE_SIZE } from "@/content/work";
import { t, type Locale } from "@/lib/i18n";
import type { WorkCardData, WorkCategory } from "@/types";
import { cn } from "@/lib/utils";

/**
 * "Our work" index: category filters derived from the projects actually
 * present, the first page of tiles, and "Show more" for the rest.
 */
export function WorkGrid({
  projects,
  categories,
  locale,
  className,
}: {
  projects: WorkCardData[];
  categories: WorkCategory[];
  locale: Locale;
  className?: string;
}) {
  const [filter, setFilter] = useState<string>("all");
  const [limit, setLimit] = useState(WORK_PAGE_SIZE);

  const visible = useMemo(
    () =>
      filter === "all"
        ? projects
        : projects.filter((project) => project.categories.includes(filter)),
    [filter, projects],
  );
  const shown = visible.slice(0, limit);

  const choose = (id: string) => {
    setFilter(id);
    setLimit(WORK_PAGE_SIZE);
  };

  if (projects.length === 0) {
    return <p className={cn("text-chalk-400", className)}>{t(ui.empty.projects, locale)}</p>;
  }

  return (
    <div className={className}>
      {categories.length > 1 ? (
        <div
          role="group"
          aria-label={t(ui.nav.services, locale)}
          className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-1 sm:mx-0 sm:flex-wrap sm:px-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {[{ id: "all", label: t(ui.labels.filterAll, locale) }, ...categories.map((c) => ({ id: c.id, label: c[locale] }))].map(
            (option) => {
              const selected = filter === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => choose(option.id)}
                  className={cn(
                    "shrink-0 rounded-button border px-4 py-2 text-[11px] font-medium tracking-[0.14em] whitespace-nowrap uppercase transition-colors duration-300",
                    selected
                      ? "border-accent bg-accent/10 text-accent"
                      : "border-line text-chalk-400 hover:border-line-strong hover:text-chalk-50",
                  )}
                >
                  {option.label}
                </button>
              );
            },
          )}
        </div>
      ) : null}

      <ul className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((project, index) => (
          <li key={project.id} className="h-full">
            <WorkCard project={project} locale={locale} priority={index < 3} className="h-full" />
          </li>
        ))}
      </ul>

      <div className="mt-10 flex flex-col items-center gap-4">
        <p className="text-[12px] tracking-[0.14em] text-chalk-500 uppercase" aria-live="polite">
          {t(ui.work.shownOf, locale)
            .replace("{shown}", String(shown.length))
            .replace("{total}", String(visible.length))}
        </p>
        {shown.length < visible.length ? (
          <Button variant="outline" size="lg" onClick={() => setLimit((n) => n + WORK_PAGE_SIZE)}>
            {t(ui.work.showMore, locale)}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
