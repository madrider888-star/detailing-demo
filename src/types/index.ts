export type ServiceCategory =
  | "protection"
  | "ppf"
  | "correction"
  | "exterior"
  | "interior"
  | "tinting";

export interface Benefit {
  title: string;
  description: string;
}

export interface ProcessStep {
  title: string;
  description: string;
  /** Optional time budget shown next to the step, e.g. "2–3 h". */
  duration?: string;
}

export interface FaqItem {
  question: string;
  answer: string;
}

export interface Service {
  slug: string;
  title: string;
  /** One-line positioning statement used on cards and hero eyebrows. */
  tagline: string;
  category: ServiceCategory;
  /** Card-length copy: two sentences maximum. */
  summary: string;
  /** Long-form intro on the detail page. */
  intro: string[];
  priceFrom: number;
  /** Human-readable job length, e.g. "3–4 days". */
  duration: string;
  warranty?: string;
  image: string;
  popular?: boolean;
  highlights: string[];
  includes: string[];
  benefits: Benefit[];
  process: ProcessStep[];
  faq: FaqItem[];
}

export interface PricingOption {
  name: string;
  description: string;
  price: number;
  /** Vehicle size tiers the price scales across. */
  note?: string;
  duration: string;
  featured?: boolean;
  serviceSlug?: string;
  includes: string[];
}

export interface PricingGroup {
  id: string;
  title: string;
  description: string;
  options: PricingOption[];
}

export type GalleryCategory =
  | "before-after"
  | "ceramic"
  | "ppf"
  | "interior"
  | "correction";

export interface GalleryItem {
  id: string;
  title: string;
  vehicle: string;
  category: GalleryCategory;
  image: string;
  /** Grid weight — wide tiles span two columns on large screens. */
  span?: "wide" | "tall";
}

export interface Testimonial {
  quote: string;
  author: string;
  vehicle: string;
  service: string;
  rating: 5 | 4;
}

export interface ComparisonPair {
  id: string;
  title: string;
  description: string;
  vehicle: string;
  before: string;
  after: string;
}

export interface NavItem {
  label: string;
  href: string;
}
