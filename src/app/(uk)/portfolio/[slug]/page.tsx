import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getWorkProject, workProjects } from "@/content/work";
import { ui } from "@/content/ui";
import { ProjectView } from "@/views/project-view";
import { t } from "@/lib/i18n";
import { pageMetadata } from "@/lib/seo";

const locale = "uk" as const;

export function generateStaticParams() {
  return workProjects.map((project) => ({ slug: project.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = getWorkProject(slug);
  if (!project) return {};

  const description =
    project.summary?.[locale] ?? project.works.map((item) => item[locale]).join(", ");

  return pageMetadata({
    locale,
    title: `${project.vehicle} — ${t(ui.nav.portfolio, locale)}`,
    description,
    path: `/portfolio/${project.slug}`,
  });
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const project = getWorkProject(slug);
  if (!project) notFound();

  return <ProjectView project={project} locale={locale} />;
}
