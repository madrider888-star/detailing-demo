import { Accordion } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { faq } from "@/content/faq";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { FaqItem } from "@/types";

export function FaqSection({
  locale,
  items = faq,
  tone = "raised",
}: {
  locale: Locale;
  items?: FaqItem[];
  tone?: "base" | "raised";
}) {
  if (items.length === 0) return null;

  return (
    <Section tone={tone} aria-labelledby="faq-title">
      <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
        <div className="lg:sticky lg:top-32 lg:self-start">
          <SectionTitle
            id="faq-title"
            eyebrow={t(ui.sections.faqEyebrow, locale)}
            title={t(ui.sections.faqTitle, locale)}
          />
          <Button
            href={localePath("/contact", locale)}
            variant="outline"
            size="sm"
            className="mt-8"
          >
            {t(ui.actions.write, locale)}
          </Button>
        </div>
        <Accordion items={items} locale={locale} />
      </div>
    </Section>
  );
}
