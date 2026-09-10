import { Hero } from "@/components/sections/hero";
import { ServiceCard } from "@/components/cards/service-card";
import { WorkCard } from "@/components/cards/work-card";
import { ProcessSteps } from "@/components/sections/process-steps";
import { ReviewsSection } from "@/components/sections/reviews-section";
import { FaqSection } from "@/components/sections/faq-section";
import { InstagramSection } from "@/components/sections/instagram-section";
import { CTASection } from "@/components/sections/cta-section";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { differentiators, materials, process } from "@/content/about";
import { featuredWork } from "@/content/work";
import { featuredServices } from "@/content/services";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";

export function HomeView({ locale }: { locale: Locale }) {
  const featured = featuredWork.slice(0, 6);

  return (
    <>
      <Hero locale={locale} />

      {featuredServices.length > 0 ? (
        <Section aria-labelledby="services-title">
          <SectionTitle
            id="services-title"
            eyebrow={t(ui.sections.servicesEyebrow, locale)}
            title={t(ui.sections.servicesTitle, locale)}
            aside={
              <Button href={localePath("/services", locale)} variant="outline">
                {t(ui.actions.allServices, locale)}
                <ArrowIcon />
              </Button>
            }
          />
          <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featuredServices.map((service, index) => (
              <Reveal as="li" key={service.slug} delay={index * 60} className="h-full">
                <ServiceCard
                  service={service}
                  locale={locale}
                  priority={index < 3}
                  className="h-full"
                />
              </Reveal>
            ))}
          </ul>
        </Section>
      ) : null}

      {featured.length > 0 ? (
        <Section tone="raised" aria-labelledby="projects-title">
          <SectionTitle
            id="projects-title"
            eyebrow={t(ui.sections.portfolioEyebrow, locale)}
            title={t(ui.sections.portfolioTitle, locale)}
            aside={
              <Button href={localePath("/portfolio", locale)} variant="outline">
                {t(ui.actions.allProjects, locale)}
                <ArrowIcon />
              </Button>
            }
          />
          <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((project, index) => (
              <Reveal as="li" key={project.slug} delay={index * 60} className="h-full">
                <WorkCard project={project} locale={locale} priority={index < 3} className="h-full" />
              </Reveal>
            ))}
          </ul>
        </Section>
      ) : null}

      {differentiators.length > 0 ? (
        <Section tone="raised" aria-labelledby="why-title">
          <SectionTitle
            id="why-title"
            eyebrow={t(ui.sections.whyEyebrow, locale)}
            title={t(ui.sections.whyTitle, locale)}
          />
          <ul className="mt-14 grid gap-px overflow-hidden rounded-card outline outline-line sm:grid-cols-2">
            {differentiators.map((item, index) => (
              <Reveal
                as="li"
                key={t(item.title, locale)}
                delay={index * 60}
                className="bg-ink-900 p-7 outline outline-line sm:p-9"
              >
                <span className="font-display text-[12px] font-medium tracking-[0.2em] text-accent">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-5 font-display text-xl font-semibold uppercase">
                  {t(item.title, locale)}
                </h3>
                <p className="mt-3 text-[15px] leading-relaxed text-chalk-400">
                  {t(item.description, locale)}
                </p>
              </Reveal>
            ))}
          </ul>
        </Section>
      ) : null}

      {process.length > 0 ? (
        <Section aria-labelledby="process-title">
          <div className="grid gap-14 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
            <div className="lg:sticky lg:top-32 lg:self-start">
              <SectionTitle
                id="process-title"
                eyebrow={t(ui.sections.processEyebrow, locale)}
                title={t(ui.sections.processTitle, locale)}
              />
            </div>
            <ProcessSteps steps={process} locale={locale} />
          </div>
        </Section>
      ) : null}

      {materials.length > 0 ? (
        <Section tone="raised" aria-labelledby="materials-title">
          <SectionTitle
            id="materials-title"
            eyebrow={t(ui.sections.materialsEyebrow, locale)}
            title={t(ui.sections.materialsTitle, locale)}
          />
          <ul className="mt-14 grid gap-px overflow-hidden rounded-card outline outline-line sm:grid-cols-2 lg:grid-cols-3">
            {materials.map((item, index) => (
              <Reveal
                as="li"
                key={t(item.name, locale)}
                delay={index * 55}
                className="bg-ink-850 p-7 outline outline-line sm:p-8"
              >
                <h3 className="font-display text-lg font-medium uppercase">
                  {t(item.name, locale)}
                </h3>
                <p className="mt-3 text-[14.5px] leading-relaxed text-chalk-400">
                  {t(item.detail, locale)}
                </p>
              </Reveal>
            ))}
          </ul>
        </Section>
      ) : null}

      <ReviewsSection locale={locale} />
      <InstagramSection locale={locale} />
      <FaqSection locale={locale} />
      <CTASection locale={locale} />
    </>
  );
}
