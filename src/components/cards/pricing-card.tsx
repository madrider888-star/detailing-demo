import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SpecList } from "@/components/ui/spec-list";
import type { PricingOption } from "@/types";
import { cn, formatPrice } from "@/lib/utils";

interface PricingCardProps {
  option: PricingOption;
  className?: string;
}

export function PricingCard({ option, className }: PricingCardProps) {
  return (
    <article
      className={cn(
        "relative flex flex-col rounded-2xl border p-7 transition-[border-color,transform] duration-500 sm:p-8",
        option.featured
          ? "border-brass-500/30 bg-carbon-800"
          : "border-white/8 bg-carbon-850 hover:border-white/16",
        className,
      )}
    >
      {option.featured ? (
        <Badge tone="accent" className="absolute -top-3 left-7 bg-carbon-800">
          Most booked
        </Badge>
      ) : null}

      <h3 className="font-display text-xl font-semibold">{option.name}</h3>
      <p className="mt-2.5 text-[14.5px] leading-relaxed text-mist-400">{option.description}</p>

      <div className="rule mt-6 flex items-baseline gap-2 pt-6">
        <span className="text-[13px] text-mist-500">from</span>
        <span className="font-display text-4xl font-semibold tracking-tight text-mist-100">
          {formatPrice(option.price)}
        </span>
      </div>
      <p className="mt-2 text-[13px] text-mist-500">
        {option.duration} in the studio
        {option.note ? ` · ${option.note}` : ""}
      </p>

      <SpecList items={option.includes} dense className="mt-7 flex-1" />

      <Button
        href={option.serviceSlug ? `/services/${option.serviceSlug}` : "/contact"}
        variant={option.featured ? "primary" : "secondary"}
        className="mt-8 w-full"
      >
        {option.serviceSlug ? "Service details" : "Request a quote"}
      </Button>
    </article>
  );
}
