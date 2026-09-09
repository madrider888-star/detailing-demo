import Image from "next/image";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Reveal } from "@/components/ui/reveal";
import { site } from "@/content/site";

export function Hero() {
  return (
    <section className="relative isolate flex min-h-[92svh] flex-col justify-end overflow-hidden pt-28 pb-14 sm:pb-16 lg:min-h-screen">
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        <Image
          src="/media/hero-studio.svg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="scale-125 object-cover object-[58%_62%] sm:scale-110 lg:scale-100 lg:object-[62%_58%]"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-carbon-950 via-carbon-950/35 to-carbon-950/75" />
        <div className="absolute inset-0 bg-gradient-to-r from-carbon-950 via-carbon-950/45 via-45% to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-carbon-950 to-transparent" />
      </div>

      <div className="shell">
        <Reveal className="max-w-3xl">
          <p className="eyebrow">
            <span aria-hidden="true" className="h-px w-8 bg-brass-600/70" />
            Odessa · Est. 2014
          </p>

          <h1 className="mt-7 text-[2.6rem] leading-[1.02] font-semibold tracking-[-0.03em] sm:text-6xl lg:text-[4.6rem]">
            Protection that keeps
            <span className="block text-mist-400">the paint you paid for.</span>
          </h1>

          <p className="mt-7 max-w-xl text-[17px] leading-relaxed text-mist-300 sm:text-lg">
            Ceramic coatings, paint protection film and measured correction — carried out in six
            climate-controlled bays by technicians who read the paint before they touch it.
          </p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button href="/contact" size="lg">
              Book Detailing
              <ArrowIcon />
            </Button>
            <Button href="/services" variant="secondary" size="lg">
              View Services
            </Button>
          </div>
        </Reveal>

        <Reveal delay={180}>
          <dl className="mt-16 grid grid-cols-2 gap-px overflow-hidden border-t border-white/10 lg:mt-24 lg:grid-cols-4">
            {site.stats.map((stat) => (
              <div key={stat.label} className="bg-carbon-950/40 py-6 pr-6 lg:py-7">
                <dt className="text-[11px] font-medium tracking-[0.2em] text-mist-500 uppercase">
                  {stat.label}
                </dt>
                <dd className="mt-2 font-display text-3xl font-semibold tracking-tight text-mist-100 lg:text-4xl">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </Reveal>
      </div>
    </section>
  );
}
