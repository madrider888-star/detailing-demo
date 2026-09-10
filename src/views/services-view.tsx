import { ServiceCard } from "@/components/cards/service-card";
import { CTASection } from "@/components/sections/cta-section";
import { FaqSection } from "@/components/sections/faq-section";
import { PageHeader } from "@/components/sections/page-header";
import { ServiceCatalog } from "@/components/sections/service-catalog";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { serviceCatalog } from "@/content/service-catalog";
import { services } from "@/content/services";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";

export function ServicesView({ locale }: { locale: Locale }) {
  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={t(ui.sections.servicesEyebrow, locale)}
        title={t(ui.sections.servicesTitle, locale)}
        description={
          serviceCatalog.length > 0
            ? t(ui.sections.servicesDescription, locale)
            : undefined
        }
      />

      {serviceCatalog.length > 0 ? (
        <Section className="pt-0 sm:pt-0 lg:pt-0">
          <ServiceCatalog groups={serviceCatalog} locale={locale} />
        </Section>
      ) : null}

      {services.length > 0 || serviceCatalog.length === 0 ? (
        <Section tone={serviceCatalog.length > 0 ? "raised" : "base"}>
          {services.length === 0 ? (
            <p className="text-chalk-400">{t(ui.empty.services, locale)}</p>
          ) : (
            <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {services.map((service, index) => (
                <Reveal
                  as="li"
                  key={service.slug}
                  delay={index * 55}
                  className="h-full"
                >
                  <ServiceCard
                    service={service}
                    locale={locale}
                    priority={index < 3}
                    className="h-full"
                  />
                </Reveal>
              ))}
            </ul>
          )}
        </Section>
      ) : null}

      <FaqSection locale={locale} />
      <CTASection locale={locale} />
    </>
  );
}
