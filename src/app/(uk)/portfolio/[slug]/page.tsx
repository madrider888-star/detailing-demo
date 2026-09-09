import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getProject, projects } from "@/content/projects";
import { ProjectView } from "@/views/project-view";
import { t } from "@/lib/i18n";
import { pageMetadata } from "@/lib/seo";

const locale = "uk" as const;

export function generateStaticParams() {
  return projects.map((project) => ({ slug: project.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = getProject(slug);
  if (!project) return {};

  return pageMetadata({
    locale,
    title: `${t(project.title, locale)} — ${project.vehicle}`,
    description: project.description[0] ? t(project.description[0], locale) : project.vehicle,
    path: `/portfolio/${project.slug}`,
  });
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const project = getProject(slug);
  if (!project) notFound();

  return <ProjectView project={project} locale={locale} />;
}
