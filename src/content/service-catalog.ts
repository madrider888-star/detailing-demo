import catalog from "./work/services.generated.json";
import type { ServiceGroup } from "@/types";

/**
 * The service catalogue shown on /services and the home page.
 *
 * It is not written by hand: scripts/build-service-catalog.mjs reads the work
 * lines of every published project in work/projects.generated.json and folds
 * the studio's many wordings of the same job into one canonical service per
 * line, grouped by the portfolio categories. Run `npm run work:services`
 * after every Instagram import to refresh it.
 *
 * Detailed service pages with prices and photos still come from services.ts;
 * this catalogue is the complete, de-duplicated list of what the studio does.
 */
export const serviceCatalog: ServiceGroup[] = catalog.groups.map((group) => ({
  id: group.id,
  uk: group.uk,
  en: group.en,
  services: group.services.map(({ id, uk, en, projects }) => ({
    id,
    uk,
    en,
    projects,
  })),
}));

export const serviceCount = serviceCatalog.reduce(
  (n, group) => n + group.services.length,
  0,
);
