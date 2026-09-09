import Image from "next/image";
import Link from "next/link";
import { ArrowIcon } from "@/components/ui/button";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { Service } from "@/types";
import { cn } from "@/lib/utils";

export function ServiceCard({
  service,
  locale,
  priority = false,
  className,
}: {
  service: Service;
  locale: Locale;
  priority?: boolean;
  className?: string;
}) {
  const price = service.price ? t(service.price, locale) : t(ui.labels.priceOnRequest, locale);

  return (
    <article
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-card border border-line bg-ink-850",
        "transition-[border-color,transform] duration-500 ease-[var(--ease-out-expo)] hover:-translate-y-1 hover:border-line-strong",
        className,
      )}
    >
      {service.cover ? (
        <div className="relative aspect-[4/3] overflow-hidden">
          <Image
            src={service.cover.src}
            alt=""
            fill
            priority={priority}
            sizes="(min-width: 1024px) 420px, (min-width: 640px) 50vw, 100vw"
            className="object-cover transition-transform duration-700 ease-[var(--ease-out-expo)] group-hover:scale-105"
          />
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-gradient-to-t from-ink-850 via-ink-850/20 to-transparent"
          />
        </div>
      ) : null}

      <div className="flex flex-1 flex-col p-6 sm:p-7">
        <p className="text-[10px] font-medium tracking-[0.22em] text-accent uppercase">
          {t(service.tagline, locale)}
        </p>
        <h3 className="mt-4 font-display text-2xl font-semibold uppercase">
          <Link
            href={localePath(`/services/${service.slug}`, locale)}
            className="before:absolute before:inset-0"
          >
            {t(service.title, locale)}
          </Link>
        </h3>
        <p className="mt-3 text-[14.5px] leading-relaxed text-chalk-400">
          {t(service.summary, locale)}
        </p>

        <dl className="rule mt-6 grid grid-cols-2 gap-4 pt-5">
          <div>
            <dt className="text-[10px] tracking-[0.18em] text-chalk-500 uppercase">
              {t(ui.labels.price, locale)}
            </dt>
            <dd className="mt-1.5 font-display text-[15px] font-medium text-chalk-50">{price}</dd>
          </div>
          {service.duration ? (
            <div>
              <dt className="text-[10px] tracking-[0.18em] text-chalk-500 uppercase">
                {t(ui.labels.duration, locale)}
              </dt>
              <dd className="mt-1.5 font-display text-[15px] font-medium text-chalk-50">
                {t(service.duration, locale)}
              </dd>
            </div>
          ) : null}
        </dl>

        <span className="mt-6 inline-flex items-center gap-2 text-[11px] font-medium tracking-[0.16em] text-chalk-200 uppercase transition-colors group-hover:text-accent">
          {t(ui.actions.viewService, locale)}
          <ArrowIcon className="transition-transform duration-300 group-hover:translate-x-1" />
        </span>
      </div>
    </article>
  );
}
