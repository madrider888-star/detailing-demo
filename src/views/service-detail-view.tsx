import Image from "next/image";
import { ServiceCard } from "@/components/cards/service-card";
import { CTASection } from "@/components/sections/cta-section";
import { PageHeader } from "@/components/sections/page-header";
import { PhotoGallery } from "@/components/sections/photo-gallery";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Accordion } from "@/components/ui/accordion";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { SpecList } from "@/components/ui/spec-list";
import { getRelatedServices } from "@/content/services";
import { faq } from "@/content/faq";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { Service } from "@/types";

export function ServiceDetailView({ service, locale }: { service: Service; locale: Locale }) {
  const related = getRelatedServices(service.slug);
  const price = service.price ? t(service.price, locale) : t(ui.labels.priceOnRequest, locale);

  const meta = [{ label: t(ui.labels.price, locale), value: price }];
  if (service.duration) {
    meta.push({ label: t(ui.labels.duration, locale), value: t(service.duration, locale) });
  }

  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={t(service.tagline, locale)}
        title={t(service.title, locale)}
        description={t(service.summary, locale)}
        media={service.cover}
        crumbs={[
          { label: t(ui.nav.home, locale), href: localePath("/", locale) },
          { label: t(ui.nav.services, locale), href: localePath("/services", locale) },
          {
            label: t(service.title, locale),
            href: localePath(`/services/${service.slug}`, locale),
          },
        ]}
        meta={meta}
      >
        <div className="mt-9">
          <Button href={localePath("/contact", locale)} size="lg">
            {t(ui.actions.book, locale)}
            <ArrowIcon />
          </Button>
        </div>
      </PageHeader>

      <Section aria-labelledby="overview-title">
        <div className="grid gap-14 lg:grid-cols-[1.15fr_0.85fr] lg:gap-20">
          <div>
            <SectionTitle
              id="overview-title"
              eyebrow={t(ui.sections.servicesEyebrow, locale)}
              title={t(service.title, locale)}
            />
            <div className="mt-8 space-y-5">
              {service.description.map((paragraph) => (
                <p
                  key={t(paragraph, locale)}
                  className="text-[16.5px] leading-relaxed text-chalk-300"
                >
                  {t(paragraph, locale)}
                </p>
              ))}
            </div>
          </div>

          {service.includes.length > 0 ? (
            <Reveal delay={120}>
              <aside className="rounded-card border border-line bg-ink-850 p-7 sm:p-8 lg:sticky lg:top-32">
                <h2 className="font-display text-lg font-medium uppercase">
                  {t(ui.labels.included, locale)}
                </h2>
                <SpecList
                  items={service.includes.map((item) => t(item, locale))}
                  dense
                  className="mt-6"
                />
                <Button href={localePath("/contact", locale)} className="mt-8 w-full">
                  {t(ui.actions.book, locale)}
                </Button>
              </aside>
            </Reveal>
          ) : null}
        </div>
      </Section>

      {service.benefits.length > 0 ? (
        <Section tone="raised" aria-labelledby="benefits-title">
          <SectionTitle
            id="benefits-title"
            eyebrow={t(ui.labels.benefits, locale)}
            title={t(ui.labels.benefits, locale)}
          />
          <ul className="mt-14 grid gap-px overflow-hidden rounded-card outline outline-line sm:grid-cols-2">
            {service.benefits.map((benefit, index) => (
              <Reveal
                as="li"
                key={t(benefit.title, locale)}
                delay={index * 60}
                className="bg-ink-900 p-7 outline outline-line sm:p-9"
              >
                <h3 className="font-display text-lg font-medium uppercase">
                  {t(benefit.title, locale)}
                </h3>
                <p className="mt-3 text-[15px] leading-relaxed text-chalk-400">
                  {t(benefit.description, locale)}
                </p>
              </Reveal>
            ))}
          </ul>
        </Section>
      ) : null}

      {service.photos.length > 0 ? (
        <Section aria-labelledby="service-photos-title">
          <SectionTitle
            id="service-photos-title"
            eyebrow={t(ui.sections.portfolioEyebrow, locale)}
            title={t(ui.sections.portfolioTitle, locale)}
          />
          <PhotoGallery photos={service.photos} locale={locale} className="mt-12" />
        </Section>
      ) : null}

      {faq.length > 0 ? (
        <Section aria-labelledby="service-faq-title">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
            <div className="lg:sticky lg:top-32 lg:self-start">
              <SectionTitle
                id="service-faq-title"
                eyebrow={t(ui.sections.faqEyebrow, locale)}
                title={t(ui.sections.faqTitle, locale)}
              />
            </div>
            <Accordion items={faq} locale={locale} />
          </div>
        </Section>
      ) : null}

      {related.length > 0 ? (
        <Section tone="raised" aria-labelledby="related-title">
          <SectionTitle
            id="related-title"
            eyebrow={t(ui.sections.servicesEyebrow, locale)}
            title={t(ui.labels.relatedServices, locale)}
          />
          <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((item) => (
              <li key={item.slug} className="h-full">
                <ServiceCard service={item} locale={locale} className="h-full" />
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      <CTASection locale={locale} media={service.cover} />
    </>
  );
}
