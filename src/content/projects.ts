import type { WorkProject } from "@/types";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  Manually added projects
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  Most projects come from Instagram through `npm run import:instagram` and
 *  live in work/projects.generated.json — do not edit that file by hand, it is
 *  rewritten on every import. Curate those in work/selection.json instead.
 *
 *  This file is for projects that were never posted on Instagram. Copy the
 *  template at the bottom into the array; photos go in public/work/<slug>/.
 */
export const manualProjects: WorkProject[] = [];

/* ─────────────────────────────────────────────────────────────────────────────
   TEMPLATE

export const example: WorkProject = {
  id: "manual-bmw-m4-2026",
  slug: "bmw-m4-manual-2026",
  vehicle: "BMW M4 Competition",
  date: "2026-05-01T00:00:00.000Z",
  sourceUrl: "",
  sources: [],
  categories: ["ppf", "tint"],            // ids from work/selection.json
  works: [
    { uk: "Повне обклеювання кузова прозорим поліуретаном", en: "Full-body clear PPF" },
  ],
  summary: { uk: "Одне речення про проєкт.", en: "One sentence about the project." },
  cover: { src: "/work/bmw-m4-manual-2026/01.jpg", width: 1600, height: 1200 },
  photos: [{ src: "/work/bmw-m4-manual-2026/01.jpg", width: 1600, height: 1200 }],
  videos: [],
  featured: false,
  order: 500,
  visible: true,
};
───────────────────────────────────────────────────────────────────────────── */
