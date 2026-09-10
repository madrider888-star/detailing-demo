import { ArrowIcon, Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { site } from "@/content/site";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";

/**
 * Instagram is where most of this studio's audience already is, so the site
 * links out rather than trying to mirror the feed.
 */
export function InstagramSection({ locale }: { locale: Locale }) {
  return (
    <Section tone="raised" aria-labelledby="instagram-title">
      <div className="flex flex-col items-start gap-10 lg:flex-row lg:items-end lg:justify-between">
        <SectionTitle
          id="instagram-title"
          eyebrow={t(ui.sections.instagramEyebrow, locale)}
          title={t(ui.sections.instagramTitle, locale)}
          description={site.instagram.handle}
        />
        <Button external={site.instagram.url} variant="outline" size="lg">
          <Icon name="instagram" className="h-4 w-4" />
          Instagram
          <ArrowIcon />
        </Button>
      </div>
    </Section>
  );
}
