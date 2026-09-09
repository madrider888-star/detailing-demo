import type { Review } from "@/types";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  Client reviews
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  TODO(client): only real reviews, published with the client's permission.
 *
 *  While this array is empty the reviews section does not render at all.
 *
 *  IMPORTANT: do not invent reviews or an average rating. Publishing fake
 *  review data in structured markup breaches Google's guidelines and can get
 *  the site penalised.
 *
 *  TEMPLATE
 *  {
 *    author: "Ім'я К.",
 *    vehicle: "Porsche 911",
 *    text: { uk: "Текст відгуку українською.", en: "Review text in English." },
 *    source: "Instagram",
 *    rating: 5,
 *  }
 */
export const reviews: Review[] = [];
