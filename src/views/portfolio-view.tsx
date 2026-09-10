import { CTASection } from "@/components/sections/cta-section";
import { PageHeader } from "@/components/sections/page-header";
import { PortfolioGrid } from "@/components/sections/portfolio-grid";
import { Section } from "@/components/ui/section";
import { projects } from "@/content/projects";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";

export function PortfolioView({ locale }: { locale: Locale }) {
  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={t(ui.sections.portfolioEyebrow, locale)}
        title={t(ui.sections.portfolioTitle, locale)}
        media={projects[0]?.cover ?? null}
      />

      <Section>
        <PortfolioGrid projects={projects} locale={locale} />
      </Section>

      <CTASection locale={locale} />
    </>
  );
}
