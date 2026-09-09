import Image from "next/image";
import { ArrowIcon, Button } from "@/components/ui/button";
import { site } from "@/content/site";

interface CTASectionProps {
  eyebrow?: string;
  title?: string;
  description?: string;
  primaryLabel?: string;
  primaryHref?: string;
  secondaryLabel?: string;
  secondaryHref?: string;
}

export function CTASection({
  eyebrow = "Next step",
  title = "Bring the car in for an assessment",
  description = "Thirty minutes under our inspection lighting tells you exactly what the paint needs — and what it does not. The assessment is free and there is no obligation to book.",
  primaryLabel = "Book Detailing",
  primaryHref = "/contact",
  secondaryLabel = "View Services",
  secondaryHref = "/services",
}: CTASectionProps) {
  return (
    <section className="relative isolate overflow-hidden border-y border-white/8">
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        <Image
          src="/media/showcase-suv.svg"
          alt=""
          fill
          sizes="100vw"
          className="object-cover object-center opacity-60"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-carbon-950 via-carbon-950/85 to-carbon-950/50" />
      </div>

      <div className="shell py-20 sm:py-24 lg:py-28">
        <div className="max-w-2xl">
          <p className="eyebrow">
            <span aria-hidden="true" className="h-px w-8 bg-brass-600/70" />
            {eyebrow}
          </p>
          <h2 className="mt-6 text-3xl leading-[1.08] font-semibold sm:text-4xl lg:text-5xl">
            {title}
          </h2>
          <p className="mt-6 text-[16.5px] leading-relaxed text-mist-300">{description}</p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button href={primaryHref} size="lg">
              {primaryLabel}
              <ArrowIcon />
            </Button>
            <Button href={secondaryHref} variant="secondary" size="lg">
              {secondaryLabel}
            </Button>
          </div>

          <p className="mt-8 text-[14px] text-mist-500">
            Or call the studio directly —{" "}
            <a
              href={`tel:${site.phoneHref}`}
              className="text-mist-200 underline decoration-white/20 underline-offset-4 transition-colors hover:text-brass-400"
            >
              {site.phone}
            </a>
          </p>
        </div>
      </div>
    </section>
  );
}
