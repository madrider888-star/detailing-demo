import { ServiceCard } from "@/components/cards/service-card";
import { CTASection } from "@/components/sections/cta-section";
import { FaqSection } from "@/components/sections/faq-section";
import { PageHeader } from "@/components/sections/page-header";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
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
      />

      <Section>
        {services.length === 0 ? (
          <p className="text-chalk-400">{t(ui.empty.services, locale)}</p>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((service, index) => (
              <Reveal as="li" key={service.slug} delay={index * 55} className="h-full">
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

      <FaqSection locale={locale} />
      <CTASection locale={locale} />
    </>
  );
}
