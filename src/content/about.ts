import type { Benefit, Photo, ProcessStep } from "@/types";
import type { LocalizedText } from "@/lib/i18n";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  About the studio
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  TODO(client): the studio's real story, approach, equipment and products.
 *
 *  Every array here is optional. An empty array hides its section, so the page
 *  stays coherent while content is still being gathered.
 */

/** Opening paragraphs on /about. */
export const story: LocalizedText[] = [];

/** Studio philosophy — the principles the work is built on. */
export const philosophy: Benefit[] = [];

/** How a car moves through the studio. Also used on the home page. */
export const process: ProcessStep[] = [];

/** Equipment the studio wants to highlight. */
export const equipment: { name: LocalizedText; detail: LocalizedText }[] = [];

/** Brands and materials used. TODO(client): confirm before publishing. */
export const materials: { name: LocalizedText; detail: LocalizedText }[] = [];

/** Photographs of the studio and the team. */
export const studioPhotos: Photo[] = [];

/** Reasons to choose THE BOX, shown on the home page. */
export const differentiators: Benefit[] = [];
