import type { MessagingLink, NavItem, OpeningHours, Photo, StudioAddress } from "@/types";
import type { LocalizedText } from "@/lib/i18n";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  THE BOX Detailing — business information
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  THIS IS THE ONLY FILE THAT CONTAINS THE STUDIO'S CONTACT DETAILS.
 *  Change the phone number here and it updates in the header, the footer, the
 *  contact page, every call button and the Google structured data at once.
 *
 *  Fields set to `null` are not yet confirmed by the client. While a field is
 *  `null` the site simply hides that element — it never shows a placeholder.
 *  Replace the `null` with a real value to switch the element on.
 *
 *  Each `{ uk: "...", en: "..." }` pair holds the Ukrainian and English version
 *  of the same text.
 */

export const site = {
  /** Displayed name. Used in the logo wordmark, page titles and structured data. */
  name: "THE BOX Detailing",
  shortName: "THE BOX",

  /**
   * Public address of the site — used for canonical links, the sitemap and
   * social cards. Change it here when the studio connects its own domain.
   */
  url: "https://detailing-demo-rho.vercel.app",

  /** TODO(client): confirm the studio's own wording for these two lines. */
  tagline: {
    uk: "Детейлінг-студія",
    en: "Detailing studio",
  } satisfies LocalizedText,

  /** Used as the fallback meta description on every page. */
  description: {
    uk: "THE BOX Detailing — студія детейлінгу та захисту лакофарбового покриття.",
    en: "THE BOX Detailing — a detailing and paint protection studio.",
  } satisfies LocalizedText,

  /* ── Contacts ─────────────────────────────────────────────────────────── */

  /**
   * Phone number, written exactly as it should be displayed. Spaces are
   * removed automatically for the "call" links. Set to null to hide it.
   */
  phone: "+380 73 774 31 58" as string | null,

  /** TODO(client): real e-mail address, e.g. "hello@example.com". */
  email: null as string | null,

  /**
   * Studio address. Each text has a Ukrainian (uk) and English (en) version.
   * To hide the address entirely, replace the whole object with:  address: null,
   *
   * TODO(client): confirm the Ukrainian spelling of the street name.
   */
  address: {
    street: { uk: "вул. Інглезі, 1Б", en: "1B Inglesi St" },
    city: { uk: "Одеса", en: "Odesa" },
    region: null,
    postalCode: null,
    country: { uk: "Україна", en: "Ukraine" },
    mapUrl: null,
  } as StudioAddress | null,

  /** TODO(client): opening hours. Leave as an empty array to hide the block. */
  hours: [] as OpeningHours[],

  /* ── Social & messaging ───────────────────────────────────────────────── */

  /** Confirmed: the studio's Instagram handle. */
  instagram: {
    handle: "@thebox.detailing",
    url: "https://www.instagram.com/thebox.detailing/",
  },

  /**
   * TODO(client): messaging links used by the header, the contact page and the
   * booking form hand-off. Add or remove entries freely.
   *
   *   { label: "Telegram",  href: "https://t.me/<username>",     icon: "telegram" }
   *   { label: "WhatsApp",  href: "https://wa.me/<number>",      icon: "whatsapp" }
   *   { label: "Viber",     href: "viber://chat?number=<number>", icon: "viber" }
   */
  messaging: [] as MessagingLink[],

  /**
   * Where the booking form sends the completed request. The form builds a
   * prefilled message and hands it to this channel — no server required.
   * Set to the index of an entry in `messaging`, or leave null to fall back to
   * e-mail (and, if there is no e-mail either, to the phone number).
   */
  bookingChannel: null as number | null,

  /* ── Home page hero ───────────────────────────────────────────────────── */

  hero: {
    /** TODO(client): confirm the headline wording with the studio. */
    headline: {
      uk: "Детейлінг\nбез компромісів",
      en: "Detailing\nwithout compromise",
    } satisfies LocalizedText,
    subline: {
      uk: "Захист лакофарбового покриття, полірування та догляд за салоном.",
      en: "Paint protection, correction and interior care.",
    } satisfies LocalizedText,
    /**
     * TODO(client): the main hero photograph.
     * Put the file in public/images/hero/ and set it here:
     *   media: { src: "/images/hero/studio.jpg", alt: { uk: "...", en: "..." } }
     * Until then the hero renders as typography on black.
     */
    media: null as Photo | null,
  },

  /* ── Facts ────────────────────────────────────────────────────────────── */

  /**
   * TODO(client): only add figures the studio can stand behind. Anything left
   * out of this array simply does not appear on the site.
   *
   *   { value: "8", label: { uk: "років досвіду", en: "years of experience" } }
   */
  stats: [] as { value: string; label: LocalizedText }[],
} as const;

/* ── Navigation ─────────────────────────────────────────────────────────── */

/** Paths have no locale prefix — it is added automatically per language. */
export const mainNav: NavItem[] = [
  { label: { uk: "Послуги", en: "Services" }, href: "/services" },
  { label: { uk: "Портфоліо", en: "Portfolio" }, href: "/portfolio" },
  { label: { uk: "Студія", en: "Studio" }, href: "/about" },
  { label: { uk: "Контакти", en: "Contact" }, href: "/contact" },
];

/** Returns the channel the booking form should hand off to, or null. */
export function bookingTarget(): MessagingLink | null {
  const index = site.bookingChannel;
  if (index === null) return null;
  return site.messaging[index] ?? null;
}

/** True when the studio has published at least one way to reach it. */
export function hasContactDetails(): boolean {
  return Boolean(site.phone || site.email || site.messaging.length > 0);
}
