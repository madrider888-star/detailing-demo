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
  /** Root-relative path, e.g. "/images/services/ceramic/01.jpg" */
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

/* ── Our work ─────────────────────────────────────────────────────────── */

/** A photo in `public/work/<slug>/`, with its pixel size for layout. */
export interface WorkPhoto {
  src: string;
  width: number;
  height: number;
  /** Instagram shortCode the frame came from. */
  source?: string;
}

/** A reel. `src` is null when the file has not been downloaded — the poster then links to Instagram. */
export interface WorkVideo {
  poster: WorkPhoto;
  src: string | null;
  sourceUrl: string;
  source?: string;
}

/** One confirmed line of work, in both languages. */
export interface WorkItem {
  uk: string;
  en: string;
  /** Set by the importer when the glossary has no translation yet. */
  untranslated?: boolean;
}

export interface WorkCategory {
  id: string;
  uk: string;
  en: string;
}

/**
 * A project in "Our work". Imported from Instagram by
 * scripts/import-instagram.mjs; manual entries use the same shape.
 */
export interface WorkProject {
  /** Stable id — the Instagram shortCode for imported projects. */
  id: string;
  /** URL segment: /portfolio/<slug> and /en/portfolio/<slug> */
  slug: string;
  /** Make and model exactly as the studio wrote it. Not translated. */
  vehicle: string;
  /** ISO date of the source post. */
  date: string;
  /** The Instagram post the project comes from. */
  sourceUrl: string;
  /** All posts merged into this project. */
  sources: string[];
  /** Category ids from selection.json — drive the filters. */
  categories: string[];
  works: WorkItem[];
  summary: LocalizedText | null;
  cover: WorkPhoto | null;
  photos: WorkPhoto[];
  videos: WorkVideo[];
  featured: boolean;
  order: number;
  visible: boolean;
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

/** Studio address. Every text field has a Ukrainian and an English version. */
export interface StudioAddress {
  street: LocalizedText;
  city: LocalizedText;
  region: LocalizedText | null;
  postalCode: string | null;
  country: LocalizedText;
  /** Optional link to Google Maps / Waze for the "Get directions" button. */
  mapUrl: string | null;
}

export interface MessagingLink {
  label: string;
  href: string;
  /** Icon key rendered by components/ui/icon.tsx */
  icon: "instagram" | "telegram" | "whatsapp" | "viber" | "phone" | "email";
}
