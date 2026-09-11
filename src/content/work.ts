import manifest from "./work/projects.generated.json";
import selection from "./work/selection.json";
import { manualProjects } from "./projects";
import type { WorkCardData, WorkCategory, WorkProject } from "@/types";

/**
 * "Our work" — the single place the site reads projects from.
 *
 * Imported projects come from work/projects.generated.json (written by
 * scripts/import-instagram.mjs), manual ones from projects.ts. A project is
 * shown only when it is visible and has a cover photo on disk, so a project
 * whose media has not been downloaded yet never renders as an empty card.
 */

export const workCategories: WorkCategory[] = selection.categories.map(({ id, uk, en }) => ({
  id,
  uk,
  en,
}));

const imported = manifest.projects as unknown as WorkProject[];

export const workProjects: WorkProject[] = [...manualProjects, ...imported]
  .filter((project) => project.visible && project.cover !== null)
  .sort((a, b) => a.order - b.order || (a.date < b.date ? 1 : -1));

export const featuredWork = workProjects.filter((project) => project.featured);

export function getWorkProject(slug: string): WorkProject | undefined {
  return workProjects.find((project) => project.slug === slug);
}

/** Categories that at least one visible project uses, in the configured order. */
export function usedWorkCategories(projects: WorkProject[] = workProjects): WorkCategory[] {
  const used = new Set(projects.flatMap((project) => project.categories));
  return workCategories.filter((category) => used.has(category.id));
}

/** How many projects the grid shows before "Show more". */
export const WORK_PAGE_SIZE = 12;

/** How many lines of work a tile previews. */
export const CARD_PREVIEW_ITEMS = 3;

/** Strips a project down to what a tile renders (no photo lists, no summaries). */
export function toCardData(project: WorkProject): WorkCardData | null {
  if (!project.cover) return null;
  return {
    id: project.id,
    slug: project.slug,
    vehicle: project.vehicle,
    categories: project.categories,
    works: project.works.slice(0, CARD_PREVIEW_ITEMS),
    worksTotal: project.works.length,
    cover: project.cover,
    hasVideo: project.videos.length > 0,
  };
}

export const workCards: WorkCardData[] = workProjects
  .map(toCardData)
  .filter((card): card is WorkCardData => card !== null);

/** Looks up the blur preview of a photo that lives in public/work. */
export function workPhotoBlur(src: string): string | undefined {
  for (const project of workProjects) {
    for (const photo of [project.cover, ...project.photos, ...project.videos.map((v) => v.poster)]) {
      if (photo?.src === src) return photo.blur;
    }
  }
  return undefined;
}
