import Image from "next/image";
import Link from "next/link";
import { ArrowIcon } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { categoryLabels } from "@/content/services";
import type { Service } from "@/types";
import { cn, formatPrice } from "@/lib/utils";

interface ServiceCardProps {
  service: Service;
  /** `feature` renders a wider card with a taller image. */
  layout?: "default" | "feature";
  priority?: boolean;
  className?: string;
}

export function ServiceCard({
  service,
  layout = "default",
  priority = false,
  className,
}: ServiceCardProps) {
  const feature = layout === "feature";

  return (
    <article
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border border-white/8 bg-carbon-850",
        "shadow-card transition-[border-color,transform] duration-500 ease-out hover:-translate-y-1 hover:border-white/18",
        className,
      )}
    >
      <div className={cn("relative overflow-hidden", feature ? "aspect-[16/10]" : "aspect-[4/3]")}>
        <Image
          src={service.image}
          alt=""
          fill
          priority={priority}
          sizes={
            feature
              ? "(min-width: 1024px) 640px, 100vw"
              : "(min-width: 1024px) 400px, (min-width: 640px) 50vw, 100vw"
          }
          className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-gradient-to-t from-carbon-850 via-carbon-850/25 to-transparent"
        />
        <div className="absolute top-4 left-4 flex gap-2">
          <Badge>{categoryLabels[service.category]}</Badge>
          {service.popular ? <Badge tone="accent">Popular</Badge> : null}
        </div>
      </div>

      <div className={cn("flex flex-1 flex-col p-6", feature && "sm:p-8")}>
        <p className="text-[11px] font-medium tracking-[0.2em] text-brass-500 uppercase">
          {service.tagline}
        </p>
        <h3
          className={cn(
            "mt-3 font-semibold tracking-tight",
            feature ? "text-2xl sm:text-[28px]" : "text-xl",
          )}
        >
          <Link href={`/services/${service.slug}`} className="before:absolute before:inset-0">
            {service.title}
          </Link>
        </h3>
        <p className="mt-3 text-[14.5px] leading-relaxed text-mist-400">{service.summary}</p>

        <dl className="rule mt-6 grid grid-cols-2 gap-4 pt-5">
          <div>
            <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">From</dt>
            <dd className="mt-1.5 font-display text-lg font-medium text-mist-100">
              {formatPrice(service.priceFrom)}
            </dd>
          </div>
          <div>
            <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">Duration</dt>
            <dd className="mt-1.5 font-display text-lg font-medium text-mist-100">
              {service.duration}
            </dd>
          </div>
        </dl>

        <span className="mt-6 inline-flex items-center gap-2 text-[13.5px] font-medium text-mist-200 transition-colors group-hover:text-brass-400">
          View service
          <ArrowIcon className="transition-transform duration-300 group-hover:translate-x-1" />
        </span>
      </div>
    </article>
  );
}
