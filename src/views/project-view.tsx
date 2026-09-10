import Image from "next/image";
import Link from "next/link";
import { WorkCard } from "@/components/cards/work-card";
import { CTASection } from "@/components/sections/cta-section";
import { PhotoGallery } from "@/components/sections/photo-gallery";
import { WorkVideoPlayer } from "@/components/sections/work-video";
import { Badge } from "@/components/ui/badge";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { SpecList } from "@/components/ui/spec-list";
import { ui } from "@/content/ui";
import { workCategories, workProjects } from "@/content/work";
import { localePath, localeTag, t, type Locale } from "@/lib/i18n";
import type { WorkProject } from "@/types";

export function ProjectView({ project, locale }: { project: WorkProject; locale: Locale }) {
  const categories = workCategories.filter((category) => project.categories.includes(category.id));
  const others = workProjects.filter((item) => item.slug !== project.slug).slice(0, 3);
  const date = new Intl.DateTimeFormat(localeTag[locale], { month: "long", year: "numeric" }).format(
    new Date(project.date),
  );

  // The cover is the first frame; the gallery shows the rest so it is not repeated.
  const galleryPhotos = project.photos.filter((photo) => photo.src !== project.cover?.src);
  const discussHref = localePath(`/contact?project=${project.slug}`, locale);

  return (
    <>
      <section className="relative isolate pt-28 pb-6 sm:pt-36 lg:pt-44">
        <div className="shell">
          <nav aria-label="Breadcrumb" className="mb-8">
            <ol className="flex flex-wrap items-center gap-2 text-[12px] tracking-[0.1em] text-chalk-500 uppercase">
              <li>
                <Link href={localePath("/", locale)} className="transition-colors hover:text-accent">
                  {t(ui.nav.home, locale)}
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li>
                <Link href={localePath("/portfolio", locale)} className="transition-colors hover:text-accent">
                  {t(ui.nav.portfolio, locale)}
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li className="text-chalk-300">{project.vehicle}</li>
            </ol>
          </nav>

          <Reveal className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end lg:gap-16">
            <div>
              <p className="eyebrow">
                <span aria-hidden="true" className="h-px w-8 bg-accent-muted" />
                {date}
              </p>
              <h1 className="display-xl mt-8 text-[2.5rem] sm:text-[3.5rem] lg:text-[4.25rem]">
                {project.vehicle}
              </h1>
              {project.summary ? (
                <p className="mt-7 max-w-2xl text-[17px] leading-relaxed text-chalk-300">
                  {t(project.summary, locale)}
                </p>
              ) : null}
              {categories.length > 0 ? (
                <ul className="mt-7 flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <li key={category.id}>
                      <Badge>{category[locale]}</Badge>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>

            <div className="flex flex-col gap-3 sm:flex-row lg:flex-col lg:items-end">
              <Button href={discussHref} size="lg">
                {t(ui.work.discussSimilar, locale)}
                <ArrowIcon />
              </Button>
              <Button external={project.sourceUrl} variant="outline" size="lg" target="_blank" rel="noreferrer noopener">
                <Icon name="instagram" className="h-4 w-4" />
                {t(ui.work.sourcePost, locale)}
              </Button>
            </div>
          </Reveal>
        </div>
      </section>

      {project.cover ? (
        <div className="shell pt-10 sm:pt-14">
          <Reveal>
            <div className="relative aspect-[4/5] w-full overflow-hidden rounded-card border border-line sm:aspect-[16/10]">
              <Image
                src={project.cover.src}
                alt={`${project.vehicle} — THE BOX Detailing`}
                fill
                priority
                sizes="(min-width: 1280px) 1360px, 100vw"
                className="object-cover"
              />
            </div>
          </Reveal>
        </div>
      ) : null}

      <Section aria-labelledby="works-title">
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
          <div className="lg:sticky lg:top-32 lg:self-start">
            <SectionTitle
              id="works-title"
              eyebrow={t(ui.work.worksDone, locale)}
              title={t(ui.work.worksDone, locale)}
            />
            <Button href={discussHref} variant="outline" size="sm" className="mt-8">
              {t(ui.work.discussSimilar, locale)}
            </Button>
          </div>
          <SpecList items={project.works.map((item) => item[locale])} />
        </div>
      </Section>

      {galleryPhotos.length > 0 ? (
        <Section tone="raised" aria-labelledby="photos-title">
          <SectionTitle id="photos-title" eyebrow={t(ui.work.photos, locale)} title={project.vehicle} />
          <PhotoGallery
            photos={galleryPhotos.map((photo, index) => ({
              src: photo.src,
              alt: {
                uk: `${project.vehicle} — фото ${index + 2}`,
                en: `${project.vehicle} — photo ${index + 2}`,
              },
            }))}
            locale={locale}
            className="mt-12"
          />
        </Section>
      ) : null}

      {project.videos.length > 0 ? (
        <Section aria-labelledby="video-title">
          <SectionTitle id="video-title" eyebrow={t(ui.work.video, locale)} title={t(ui.work.video, locale)} />
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {project.videos.map((video) => (
              <WorkVideoPlayer
                key={video.poster.src}
                video={video}
                vehicle={project.vehicle}
                locale={locale}
                className="max-w-sm"
              />
            ))}
          </div>
        </Section>
      ) : null}

      {others.length > 0 ? (
        <Section tone="raised" aria-labelledby="more-work-title">
          <SectionTitle
            id="more-work-title"
            eyebrow={t(ui.sections.portfolioEyebrow, locale)}
            title={t(ui.work.moreWork, locale)}
            aside={
              <Button href={localePath("/portfolio", locale)} variant="outline">
                {t(ui.work.backToWork, locale)}
                <ArrowIcon />
              </Button>
            }
          />
          <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {others.map((item) => (
              <li key={item.id} className="h-full">
                <WorkCard project={item} locale={locale} className="h-full" />
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      <CTASection locale={locale} />
    </>
  );
}
