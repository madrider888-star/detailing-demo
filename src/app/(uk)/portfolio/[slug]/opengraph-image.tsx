import { getWorkProject, workProjects } from "@/content/work";
import { OG_CONTENT_TYPE, OG_SIZE, projectOgImage, siteOgImage } from "@/lib/og";

const locale = "uk" as const;

export const alt = "THE BOX Detailing";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export function generateStaticParams() {
  return workProjects.map((project) => ({ slug: project.slug }));
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const project = getWorkProject(slug);
  return project ? projectOgImage(project, locale) : siteOgImage(locale);
}
