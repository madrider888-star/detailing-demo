import type { Service } from "@/types";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  Services
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  TODO(client): the real service list has not been supplied yet.
 *
 *  HOW TO ADD A SERVICE
 *  1. Put the photos in  public/images/services/<slug>/
 *  2. Copy the template at the bottom of this file into the array below.
 *  3. Give it a unique `slug` — it becomes the page address:
 *       /services/<slug>      (Ukrainian)
 *       /en/services/<slug>   (English)
 *  4. Fill in both `uk` and `en` for every text field.
 *  5. Leave `price: null` to show "Ціна за запитом" / "Contact for price".
 *
 *  The service appears automatically on /services, in the home page grid (if
 *  `featured: true`), in the booking form dropdown and in the sitemap.
 */
export const services: Service[] = [];

export const featuredServices = services.filter((service) => service.featured);

export function getService(slug: string): Service | undefined {
  return services.find((service) => service.slug === slug);
}

export function getRelatedServices(slug: string, limit = 3): Service[] {
  return services.filter((service) => service.slug !== slug).slice(0, limit);
}

/* ─────────────────────────────────────────────────────────────────────────────
   TEMPLATE — copy this into the array above and fill it in.

export const example: Service = {
  slug: "ceramic-coating",
  title: { uk: "Керамічне покриття", en: "Ceramic Coating" },
  tagline: { uk: "Захист лакофарбового покриття", en: "Paint protection" },
  summary: {
    uk: "Коротко, одне-два речення для картки послуги.",
    en: "Two sentences maximum, shown on the service card.",
  },
  description: [
    { uk: "Перший абзац на сторінці послуги.", en: "First paragraph on the service page." },
    { uk: "Другий абзац.", en: "Second paragraph." },
  ],
  includes: [
    { uk: "Перший пункт переліку робіт", en: "First item in the list of work" },
    { uk: "Другий пункт", en: "Second item" },
  ],
  benefits: [
    {
      title: { uk: "Заголовок переваги", en: "Benefit heading" },
      description: { uk: "Пояснення у 1–2 реченнях.", en: "One or two sentences." },
    },
  ],
  duration: { uk: "3–4 дні", en: "3–4 days" },
  price: null, // or { uk: "від 12 000 ₴", en: "from ₴12,000" }
  cover: {
    src: "/images/services/ceramic-coating/cover.jpg",
    alt: { uk: "Опис фото українською", en: "Photo description in English" },
  },
  photos: [],
  featured: true,
};
───────────────────────────────────────────────────────────────────────────── */
