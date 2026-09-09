import { CTASection } from "@/components/sections/cta-section";
import { PageHeader } from "@/components/sections/page-header";
import { PhotoGallery } from "@/components/sections/photo-gallery";
import { ProcessSteps } from "@/components/sections/process-steps";
import { InstagramSection } from "@/components/sections/instagram-section";
import { ReviewsSection } from "@/components/sections/reviews-section";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { equipment, materials, philosophy, process, story, studioPhotos } from "@/content/about";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";

export function AboutView({ locale }: { locale: Locale }) {
  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={t(ui.nav.about, locale)}
        title={t(ui.sections.whyTitle, locale)}
        media={studioPhotos[0] ?? null}
      />

      {story.length > 0 ? (
        <Section>
          <div className="max-w-3xl space-y-6">
            {story.map((paragraph) => (
              <p
                key={t(paragraph, locale)}
                className="text-[17px] leading-relaxed text-chalk-300"
              >
                {t(paragraph, locale)}
              </p>
            ))}
          </div>
        </Section>
      ) : null}

      {philosophy.length > 0 ? (
        <Section tone="raised" aria-labelledby="philosophy-title">
          <SectionTitle
            id="philosophy-title"
            eyebrow={t(ui.sections.whyEyebrow, locale)}
            title={t(ui.sections.whyTitle, locale)}
          />
          <ul className="mt-14 grid gap-px overflow-hidden rounded-card outline outline-line sm:grid-cols-2">
            {philosophy.map((item, index) => (
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
        <Section aria-labelledby="about-process">
          <div className="grid gap-14 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
            <div className="lg:sticky lg:top-32 lg:self-start">
              <SectionTitle
                id="about-process"
                eyebrow={t(ui.sections.processEyebrow, locale)}
                title={t(ui.sections.processTitle, locale)}
              />
            </div>
            <ProcessSteps steps={process} locale={locale} />
          </div>
        </Section>
      ) : null}

      {(equipment.length > 0 || materials.length > 0) ? (
        <Section tone="raised" aria-labelledby="equipment-title">
          <div className="grid gap-14 lg:grid-cols-2 lg:gap-16">
            {equipment.length > 0 ? (
              <div>
                <SectionTitle
                  id="equipment-title"
                  eyebrow={t(ui.sections.materialsEyebrow, locale)}
                  title={t(ui.sections.materialsTitle, locale)}
                />
                <ul className="mt-10 divide-y divide-line border-y border-line">
                  {equipment.map((item) => (
                    <li key={t(item.name, locale)} className="py-5">
                      <p className="font-display text-[16px] font-medium text-chalk-50">
                        {t(item.name, locale)}
                      </p>
                      <p className="mt-1.5 text-[14.5px] leading-relaxed text-chalk-400">
                        {t(item.detail, locale)}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {materials.length > 0 ? (
              <div>
                <SectionTitle
                  eyebrow={t(ui.sections.materialsEyebrow, locale)}
                  title={t(ui.sections.materialsTitle, locale)}
                />
                <ul className="mt-10 divide-y divide-line border-y border-line">
                  {materials.map((item) => (
                    <li key={t(item.name, locale)} className="py-5">
                      <p className="font-display text-[16px] font-medium text-chalk-50">
                        {t(item.name, locale)}
                      </p>
                      <p className="mt-1.5 text-[14.5px] leading-relaxed text-chalk-400">
                        {t(item.detail, locale)}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </Section>
      ) : null}

      {studioPhotos.length > 0 ? (
        <Section>
          <PhotoGallery photos={studioPhotos} locale={locale} />
        </Section>
      ) : null}

      <ReviewsSection locale={locale} />
      <InstagramSection locale={locale} />
      <CTASection locale={locale} />
    </>
  );
}
