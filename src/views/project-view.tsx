import { BeforeAfter } from "@/components/sections/before-after";
import { CTASection } from "@/components/sections/cta-section";
import { PageHeader } from "@/components/sections/page-header";
import { PhotoGallery } from "@/components/sections/photo-gallery";
import { ProjectCard } from "@/components/cards/project-card";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { projects } from "@/content/projects";
import { services } from "@/content/services";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { Project } from "@/types";

export function ProjectView({ project, locale }: { project: Project; locale: Locale }) {
  const performed = project.serviceSlugs
    .map((slug) => services.find((service) => service.slug === slug))
    .filter((service) => service !== undefined);

  const others = projects.filter((item) => item.slug !== project.slug).slice(0, 3);

  const meta = [{ label: t(ui.labels.vehicle, locale), value: project.vehicle }];
  if (project.year) meta.push({ label: t(ui.labels.year, locale), value: project.year });
  if (performed.length > 0) {
    meta.push({
      label: t(ui.labels.servicesPerformed, locale),
      value: performed.map((service) => t(service.title, locale)).join(", "),
    });
  }

  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={project.vehicle}
        title={t(project.title, locale)}
        media={project.cover}
        crumbs={[
          { label: t(ui.nav.home, locale), href: localePath("/", locale) },
          { label: t(ui.nav.portfolio, locale), href: localePath("/portfolio", locale) },
          {
            label: t(project.title, locale),
            href: localePath(`/portfolio/${project.slug}`, locale),
          },
        ]}
        meta={meta}
      />

      {project.description.length > 0 ? (
        <Section aria-labelledby="project-overview">
          <div className="grid gap-12 lg:grid-cols-[1fr_0.6fr] lg:gap-20">
            <div>
              <h2 id="project-overview" className="sr-only">
                {t(project.title, locale)}
              </h2>
              <div className="space-y-5">
                {project.description.map((paragraph) => (
                  <p
                    key={t(paragraph, locale)}
                    className="text-[16.5px] leading-relaxed text-chalk-300"
                  >
                    {t(paragraph, locale)}
                  </p>
                ))}
              </div>
            </div>

            {performed.length > 0 ? (
              <aside className="rounded-card border border-line bg-ink-850 p-7">
                <h3 className="text-[10px] font-medium tracking-[0.22em] text-chalk-500 uppercase">
                  {t(ui.labels.servicesPerformed, locale)}
                </h3>
                <ul className="mt-5 space-y-3">
                  {performed.map((service) => (
                    <li key={service.slug}>
                      <Button
                        href={localePath(`/services/${service.slug}`, locale)}
                        variant="ghost"
                        size="sm"
                        className="px-0"
                      >
                        {t(service.title, locale)}
                        <ArrowIcon />
                      </Button>
                    </li>
                  ))}
                </ul>
              </aside>
            ) : null}
          </div>
        </Section>
      ) : null}

      {project.beforeAfter.length > 0 ? (
        <Section tone="raised" aria-labelledby="project-compare">
          <SectionTitle
            id="project-compare"
            eyebrow={t(ui.sections.beforeAfterEyebrow, locale)}
            title={t(ui.sections.beforeAfterTitle, locale)}
            description={t(ui.labels.dragToCompare, locale)}
          />
          <div className="mt-12 grid gap-10 lg:grid-cols-2">
            {project.beforeAfter.map((pair, index) => (
              <Reveal key={pair.before.src} delay={index * 80}>
                <BeforeAfter
                  before={pair.before}
                  after={pair.after}
                  beforeLabel={t(ui.labels.before, locale)}
                  afterLabel={t(ui.labels.after, locale)}
                  caption={t(pair.caption, locale)}
                  locale={locale}
                  priority={index === 0}
                />
                <p className="mt-4 text-[14.5px] text-chalk-400">{t(pair.caption, locale)}</p>
              </Reveal>
            ))}
          </div>
        </Section>
      ) : null}

      {project.photos.length > 0 ? (
        <Section aria-labelledby="project-photos">
          <SectionTitle
            id="project-photos"
            eyebrow={t(ui.sections.portfolioEyebrow, locale)}
            title={project.vehicle}
          />
          <PhotoGallery photos={project.photos} locale={locale} className="mt-12" />
        </Section>
      ) : null}

      {others.length > 0 ? (
        <Section tone="raised" aria-labelledby="other-projects">
          <SectionTitle
            id="other-projects"
            eyebrow={t(ui.sections.portfolioEyebrow, locale)}
            title={t(ui.labels.moreProjects, locale)}
            aside={
              <Button href={localePath("/portfolio", locale)} variant="outline">
                {t(ui.actions.backToPortfolio, locale)}
                <ArrowIcon />
              </Button>
            }
          />
          <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {others.map((item) => (
              <li key={item.slug}>
                <ProjectCard project={item} locale={locale} />
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      <CTASection locale={locale} media={project.cover} />
    </>
  );
}
