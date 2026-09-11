import Image from "next/image";
import Link from "next/link";
import { Reveal } from "@/components/ui/reveal";
import { t, type Locale } from "@/lib/i18n";
import type { Photo } from "@/types";
import { cn } from "@/lib/utils";

interface Crumb {
  label: string;
  href: string;
}

/** Shared hero band for every route except the home page. */
export function PageHeader({
  locale,
  eyebrow,
  title,
  description,
  media,
  crumbs,
  meta,
  children,
  className,
}: {
  locale: Locale;
  eyebrow: string;
  title: string;
  description?: string;
  media?: Photo | null;
  crumbs?: Crumb[];
  meta?: { label: string; value: string }[];
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "relative isolate overflow-hidden pt-28 pb-16 sm:pt-36 sm:pb-20 lg:pt-44 lg:pb-24",
        className,
      )}
    >
      {media ? (
        <div aria-hidden="true" className="absolute inset-0 -z-10">
          <Image
            src={media.src}
            alt=""
            fill
            priority
            placeholder={media.blur ? "blur" : "empty"}
            blurDataURL={media.blur}
            sizes="100vw"
            className="parallax-media object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-ink-950 via-ink-950/80 to-ink-950" />
        </div>
      ) : null}

      <div className="shell">
        {crumbs ? (
          <nav aria-label="Breadcrumb" className="mb-8">
            <ol className="flex flex-wrap items-center gap-2 text-[12px] tracking-[0.1em] text-chalk-500 uppercase">
              {crumbs.map((crumb, index) => (
                <li key={crumb.href} className="flex items-center gap-2">
                  {index > 0 ? <span aria-hidden="true">/</span> : null}
                  <Link href={crumb.href} className="transition-colors hover:text-accent">
                    {crumb.label}
                  </Link>
                </li>
              ))}
            </ol>
          </nav>
        ) : null}

        <Reveal className="max-w-4xl">
          <p className="eyebrow">
            <span aria-hidden="true" className="h-px w-8 bg-accent-muted" />
            {eyebrow}
          </p>
          <h1 className="display-xl mt-8 text-[2.5rem] sm:text-[3.5rem] lg:text-[4.5rem]">
            {title}
          </h1>
          {description ? (
            <p className="mt-7 max-w-2xl text-[17px] leading-relaxed text-chalk-300">
              {description}
            </p>
          ) : null}
          {children}
        </Reveal>

        {meta && meta.length > 0 ? (
          <Reveal delay={140}>
            <dl className="mt-14 grid grid-cols-2 gap-px border-t border-line lg:grid-cols-4">
              {meta.map((item) => (
                <div key={item.label} className="py-6 pr-6">
                  <dt className="text-[10px] font-medium tracking-[0.22em] text-chalk-500 uppercase">
                    {item.label}
                  </dt>
                  <dd lang={locale} className="mt-2 font-display text-xl font-semibold text-chalk-50 lg:text-2xl">
                    {item.value}
                  </dd>
                </div>
              ))}
            </dl>
          </Reveal>
        ) : null}
      </div>
    </section>
  );
}
