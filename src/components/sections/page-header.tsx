import Image from "next/image";
import Link from "next/link";
import { Reveal } from "@/components/ui/reveal";
import { cn } from "@/lib/utils";

interface Crumb {
  label: string;
  href: string;
}

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  image?: string;
  crumbs?: Crumb[];
  /** Optional stat/meta row rendered under the description. */
  meta?: { label: string; value: string }[];
  children?: React.ReactNode;
  className?: string;
}

/** Shared hero band for every route except the home page. */
export function PageHeader({
  eyebrow,
  title,
  description,
  image,
  crumbs,
  meta,
  children,
  className,
}: PageHeaderProps) {
  return (
    <section className={cn("relative isolate overflow-hidden pt-32 pb-16 sm:pt-40 sm:pb-20 lg:pt-48 lg:pb-24", className)}>
      {image ? (
        <div aria-hidden="true" className="absolute inset-0 -z-10">
          <Image src={image} alt="" fill priority sizes="100vw" className="object-cover opacity-45" />
          <div className="absolute inset-0 bg-gradient-to-b from-carbon-950 via-carbon-950/85 to-carbon-950" />
          <div className="absolute inset-0 bg-gradient-to-r from-carbon-950 via-carbon-950/60 to-transparent" />
        </div>
      ) : null}

      <div className="shell">
        {crumbs ? (
          <nav aria-label="Breadcrumb" className="mb-8">
            <ol className="flex flex-wrap items-center gap-2 text-[13px] text-mist-500">
              {crumbs.map((crumb, index) => (
                <li key={crumb.href} className="flex items-center gap-2">
                  {index > 0 ? <span aria-hidden="true">/</span> : null}
                  <Link href={crumb.href} className="transition-colors hover:text-mist-200">
                    {crumb.label}
                  </Link>
                </li>
              ))}
            </ol>
          </nav>
        ) : null}

        <Reveal className="max-w-3xl">
          <p className="eyebrow">
            <span aria-hidden="true" className="h-px w-8 bg-brass-600/70" />
            {eyebrow}
          </p>
          <h1 className="mt-6 text-4xl leading-[1.05] font-semibold tracking-[-0.03em] sm:text-5xl lg:text-[3.75rem]">
            {title}
          </h1>
          <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-mist-300">{description}</p>
          {children}
        </Reveal>

        {meta ? (
          <Reveal delay={140}>
            <dl className="mt-14 grid grid-cols-2 gap-px border-t border-white/10 lg:grid-cols-4">
              {meta.map((item) => (
                <div key={item.label} className="py-6 pr-6">
                  <dt className="text-[11px] font-medium tracking-[0.2em] text-mist-500 uppercase">
                    {item.label}
                  </dt>
                  <dd className="mt-2 font-display text-2xl font-semibold text-mist-100 lg:text-3xl">
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
