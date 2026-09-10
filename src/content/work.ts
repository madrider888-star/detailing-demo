import manifest from "./work/projects.generated.json";
import selection from "./work/selection.json";
import { manualProjects } from "./projects";
import type { WorkCategory, WorkProject } from "@/types";

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
