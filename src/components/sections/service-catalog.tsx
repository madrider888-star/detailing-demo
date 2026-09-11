import Link from "next/link";
import { ArrowIcon } from "@/components/ui/button";
import { Reveal } from "@/components/ui/reveal";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { ServiceGroup } from "@/types";
import { cn } from "@/lib/utils";

/**
 * The de-duplicated list of everything the studio does, grouped by category.
 *
 * `full` (the /services page) lists every service in a column next to its
 * group name. `compact` (the home page) shows each group as a card with its
 * most frequent services and a link to the full list.
 */
export function ServiceCatalog({
  groups,
  locale,
  variant = "full",
  className,
}: {
  groups: ServiceGroup[];
  locale: Locale;
  variant?: "full" | "compact";
  className?: string;
}) {
  if (groups.length === 0) return null;

  if (variant === "compact") {
    const PREVIEW = 4;
    return (
      <ul
        className={cn(
          "grid gap-px overflow-hidden sm:grid-cols-2 lg:grid-cols-3",
          className,
        )}
      >
        {groups.map((group, index) => {
          const preview = group.services.slice(0, PREVIEW);
          const rest = group.services.length - preview.length;
          return (
            <Reveal
              as="li"
              key={group.id}
              delay={index * 60}
              className="flex flex-col bg-ink-850 p-7 outline outline-line sm:p-8"
            >
              <p className="font-display text-[13px] font-medium tracking-[0.2em] text-accent">
                {String(index + 1).padStart(2, "0")}
              </p>
              <h3 className="mt-5 font-display text-xl font-semibold uppercase">
                {group[locale]}
              </h3>
              <ul className="mt-5 space-y-2.5 text-[14.5px] leading-snug text-chalk-300">
                {preview.map((service) => (
                  <li key={service.id} className="flex gap-3">
                    <span
                      aria-hidden="true"
                      className="mt-[0.7em] h-px w-3 shrink-0 bg-accent-muted"
                    />
                    <span>{service[locale]}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={`${localePath("/services", locale)}#${group.id}`}
                className="group mt-auto inline-flex items-center gap-2 pt-7 text-[11px] font-medium tracking-[0.18em] text-chalk-400 uppercase transition-colors hover:text-accent"
              >
                {rest > 0
                  ? t(ui.actions.moreServices, locale).replace(
                      "{count}",
                      String(rest),
                    )
                  : t(ui.actions.allServices, locale)}
                <ArrowIcon />
              </Link>
            </Reveal>
          );
        })}
      </ul>
    );
  }

  return (
    <div className={cn("divide-y divide-line border-y border-line", className)}>
      {groups.map((group, index) => (
        <section
          key={group.id}
          id={group.id}
          aria-labelledby={`${group.id}-title`}
          className="scroll-mt-28 py-12 lg:py-16"
        >
          <Reveal
            delay={Math.min(index, 3) * 60}
            className="grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16"
          >
            <div className="lg:sticky lg:top-32 lg:self-start">
              <p className="font-display text-[13px] font-medium tracking-[0.2em] text-accent">
                {String(index + 1).padStart(2, "0")}
              </p>
              <h2
                id={`${group.id}-title`}
                className="mt-4 font-display text-[1.75rem] leading-tight font-semibold uppercase sm:text-[2.25rem]"
              >
                {group[locale]}
              </h2>
              <Link
                href={`${localePath("/portfolio", locale)}#${group.id}`}
                className="group mt-6 inline-flex items-center gap-2 text-[11px] font-medium tracking-[0.18em] text-chalk-300 uppercase transition-colors hover:text-accent"
              >
                {t(ui.actions.viewCategoryWork, locale)}
                <ArrowIcon />
              </Link>
            </div>

            <ol className="divide-y divide-line/60">
              {group.services.map((service) => (
                <li key={service.id} className="py-4 first:pt-0 last:pb-0">
                  <span className="text-[16px] leading-snug text-chalk-100 sm:text-[17px]">
                    {service[locale]}
                  </span>
                </li>
              ))}
            </ol>
          </Reveal>
        </section>
      ))}
    </div>
  );
}
