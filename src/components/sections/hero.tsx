import Image from "next/image";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Reveal } from "@/components/ui/reveal";
import { site } from "@/content/site";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function Hero({ locale }: { locale: Locale }) {
  const media = site.hero.media;
  const headline = t(site.hero.headline, locale);

  return (
    <section
      className={cn(
        "relative isolate flex flex-col justify-end overflow-hidden pt-32 pb-14 sm:pb-20",
        // Full-bleed height is only worth reserving once there is a photograph.
        media ? "min-h-[92svh] lg:min-h-screen" : "min-h-[68svh]",
      )}
    >
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        {media ? (
          <>
            <Image
              src={media.src}
              alt=""
              fill
              priority
              sizes="100vw"
              className="object-cover object-center"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-ink-950 via-ink-950/45 to-ink-950/70" />
            <div className="absolute inset-0 bg-gradient-to-r from-ink-950 via-ink-950/40 to-transparent" />
          </>
        ) : (
          <div className="absolute inset-0 bg-ink-950" />
        )}
      </div>

      <div className="shell">
        <Reveal className="max-w-4xl">
          <p className="eyebrow">
            <span aria-hidden="true" className="h-px w-10 bg-accent-muted" />
            {site.instagram.handle}
          </p>

          <h1 className="display-xl mt-10 text-[3rem] sm:mt-12 whitespace-pre-line sm:text-[4.5rem] lg:text-[6rem]">
            {headline}
          </h1>

          <p className="mt-8 max-w-xl text-[17px] leading-relaxed text-chalk-300 sm:text-lg">
            {t(site.hero.subline, locale)}
          </p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button href={localePath("/contact", locale)} size="lg">
              {t(ui.actions.book, locale)}
              <ArrowIcon />
            </Button>
            <Button href={localePath("/portfolio", locale)} variant="outline" size="lg">
              {t(ui.actions.viewPortfolio, locale)}
            </Button>
          </div>
        </Reveal>

        {site.stats.length > 0 ? (
          <Reveal delay={180}>
            <dl className="mt-16 grid grid-cols-2 gap-px border-t border-line lg:mt-24 lg:grid-cols-4">
              {site.stats.map((stat) => (
                <div key={stat.value} className="py-6 pr-6 lg:py-8">
                  <dt className="text-[10px] font-medium tracking-[0.22em] text-chalk-500 uppercase">
                    {t(stat.label, locale)}
                  </dt>
                  <dd className="mt-2 font-display text-3xl font-semibold text-chalk-50 lg:text-4xl">
                    {stat.value}
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
