import type { Project } from "@/types";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  Portfolio projects
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  TODO(client): real project photography has not been supplied yet.
 *
 *  HOW TO ADD A PROJECT
 *  1. Create a folder:  public/images/portfolio/<slug>/
 *  2. Drop the photos in. Any file names work — you reference them below.
 *  3. Copy the template at the bottom of this file into the array.
 *  4. `serviceSlugs` must match slugs from services.ts — that is what links the
 *     project to the services it used, in both directions.
 *  5. `beforeAfter` pairs power the drag-to-compare slider. Leave the array
 *     empty if there are no matched pairs for this car.
 *
 *  The project appears automatically on /portfolio, gets its own page at
 *  /portfolio/<slug>, shows on the home page when `featured: true`, and is
 *  added to the sitemap.
 */
export const projects: Project[] = [];

export const featuredProjects = projects.filter((project) => project.featured);

export function getProject(slug: string): Project | undefined {
  return projects.find((project) => project.slug === slug);
}

export function getProjectsByService(serviceSlug: string): Project[] {
  return projects.filter((project) => project.serviceSlugs.includes(serviceSlug));
}

/** Every before/after pair across the portfolio, for the home page section. */
export function allBeforeAfterPairs() {
  return projects.flatMap((project) =>
    project.beforeAfter.map((pair) => ({ project, pair })),
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   TEMPLATE — copy this into the array above and fill it in.

export const example: Project = {
  slug: "bmw-m4-competition",
  title: { uk: "Повний захист кузова", en: "Full body protection" },
  vehicle: "BMW M4 Competition",
  year: "2023",
  serviceSlugs: ["ceramic-coating"],
  description: [
    { uk: "Що саме робили і чому.", en: "What was done and why." },
  ],
  cover: {
    src: "/images/portfolio/bmw-m4-competition/cover.jpg",
    alt: { uk: "BMW M4 після полірування", en: "BMW M4 after polishing" },
  },
  photos: [
    {
      src: "/images/portfolio/bmw-m4-competition/01.jpg",
      alt: { uk: "Деталь переднього крила", en: "Front wing detail" },
    },
  ],
  beforeAfter: [
    {
      before: { src: "/images/portfolio/bmw-m4-competition/before-01.jpg", alt: { uk: "До полірування", en: "Before polishing" } },
      after: { src: "/images/portfolio/bmw-m4-competition/after-01.jpg", alt: { uk: "Після полірування", en: "After polishing" } },
      caption: { uk: "Капот після двоетапної полірування", en: "Bonnet after two-stage correction" },
    },
  ],
  featured: true,
};
───────────────────────────────────────────────────────────────────────────── */
