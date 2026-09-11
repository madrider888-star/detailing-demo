import { CTASection } from "@/components/sections/cta-section";
import { PageHeader } from "@/components/sections/page-header";
import { WorkGrid } from "@/components/sections/work-grid";
import { Section } from "@/components/ui/section";
import { ui } from "@/content/ui";
import { usedWorkCategories, workCards, workProjects } from "@/content/work";
import { t, type Locale } from "@/lib/i18n";

export function PortfolioView({ locale }: { locale: Locale }) {
  const first = workProjects[0];

  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={t(ui.sections.portfolioEyebrow, locale)}
        title={t(ui.sections.portfolioTitle, locale)}
        media={
          first?.cover
            ? { src: first.cover.src, alt: { uk: first.vehicle, en: first.vehicle }, blur: first.cover.blur }
            : null
        }
      />

      <Section>
        <WorkGrid projects={workCards} categories={usedWorkCategories()} locale={locale} />
      </Section>

      <CTASection locale={locale} />
    </>
  );
}
