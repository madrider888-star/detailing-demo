import type { LocalizedText } from "@/lib/i18n";

/**
 * Content model for THE BOX Detailing.
 *
 * Every field a non-developer edits lives in `src/content`. Anything typed
 * `| null` is optional on purpose: the UI hides the element rather than showing
 * a placeholder, so the site never displays information the studio has not
 * confirmed.
 */

/** A photograph in `public/images/...`. Rendered with `fill`, so no dimensions needed. */
export interface Photo {
  /** Root-relative path, e.g. "/images/portfolio/bmw-m4/01.jpg" */
  src: string;
  /** Describe what is in the photo, in both languages, for screen readers and SEO. */
  alt: LocalizedText;
}

export interface Benefit {
  title: LocalizedText;
  description: LocalizedText;
}

export interface ProcessStep {
  title: LocalizedText;
  description: LocalizedText;
  duration?: LocalizedText;
}

export interface FaqItem {
  question: LocalizedText;
  answer: LocalizedText;
}

export interface Service {
  /** URL segment, shared by both languages: /services/<slug> and /en/services/<slug> */
  slug: string;
  title: LocalizedText;
  /** One short line shown above the title on cards and the detail hero. */
  tagline: LocalizedText;
  /** Two sentences maximum — used on cards. */
  summary: LocalizedText;
  /** Long-form paragraphs on the service page. */
  description: LocalizedText[];
  /** Bullet list of what the job covers. */
  includes: LocalizedText[];
  benefits: Benefit[];
  /** How long the car stays in the studio, e.g. { uk: "3–4 дні", en: "3–4 days" }. */
  duration: LocalizedText | null;
  /** Leave null to display "Contact for price". Set it to show a real figure. */
  price: LocalizedText | null;
  cover: Photo | null;
  photos: Photo[];
  /** Featured services appear on the home page. */
  featured: boolean;
}

export interface BeforeAfterPair {
  before: Photo;
  after: Photo;
  caption: LocalizedText;
}

export interface Project {
  /** URL segment: /portfolio/<slug> and /en/portfolio/<slug> */
  slug: string;
  title: LocalizedText;
  /** Make and model — the same in both languages, so not translated. */
  vehicle: string;
  /** Optional model year or the year the work was done. */
  year: string | null;
  /** Slugs from services.ts — used to cross-link the project to its services. */
  serviceSlugs: string[];
  description: LocalizedText[];
  cover: Photo | null;
  photos: Photo[];
  beforeAfter: BeforeAfterPair[];
  /** Featured projects appear on the home page. */
  featured: boolean;
}

export interface Review {
  author: string;
  vehicle: string | null;
  text: LocalizedText;
  /** Where the review came from, e.g. "Instagram", "Google". */
  source: string | null;
  rating: 1 | 2 | 3 | 4 | 5 | null;
}

export interface NavItem {
  label: LocalizedText;
  /** Locale-free path; the locale prefix is added at render time. */
  href: string;
}

export interface OpeningHours {
  days: LocalizedText;
  time: LocalizedText;
}

export interface MessagingLink {
  label: string;
  href: string;
  /** Icon key rendered by components/ui/icon.tsx */
  icon: "instagram" | "telegram" | "whatsapp" | "viber" | "phone" | "email";
}
