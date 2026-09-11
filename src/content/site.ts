import type { HeroVideo, MessagingLink, NavItem, OpeningHours, Photo, StudioAddress } from "@/types";
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
    /** Opens a direct message to the studio's account. */
    dm: "https://ig.me/m/thebox.detailing",
  },

  /**
   * Messaging links used by the header, the contact page, the mobile action
   * bar and the booking form hand-off. Add or remove entries freely.
   *
   *   { label: "Telegram",  href: "https://t.me/<username>",     icon: "telegram" }
   *   { label: "WhatsApp",  href: "https://wa.me/<number>",      icon: "whatsapp" }
   *   { label: "Viber",     href: "viber://chat?number=<number>", icon: "viber" }
   *
   * The studio's Telegram is the account on its phone number: the link opens
   * a direct chat. Only the label is shown on the site, never the link.
   */
  messaging: [
    { label: "Telegram", href: "https://t.me/+380737743158", icon: "telegram" },
  ] as MessagingLink[],

  /**
   * Where the booking form sends the completed request. The form builds a
   * prefilled message and opens this channel with it — a personal chat, no
   * bot and no server. Telegram and WhatsApp links get the text prefilled;
   * other channels open plain, with the text ready to paste.
   * Set to the index of an entry in `messaging`, or leave null to fall back to
   * e-mail (and, if there is no e-mail either, to the phone number).
   */
  bookingChannel: 0 as number | null,

  /**
   * How the booking form delivers requests:
   *   "messenger" — opens the chat from `bookingChannel` with the text (default)
   *   "bot"       — posts to /api/lead, which needs TELEGRAM_BOT_TOKEN and
   *                 TELEGRAM_CHAT_ID in the hosting environment
   */
  leads: "messenger" as "messenger" | "bot",

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
    /**
     * Background clip behind the headline. Any short reel from public/work
     * works; keep it under ~3 MB. Set to null for a still photograph (media)
     * or plain black. The poster is shown until the clip plays and instead of
     * it for visitors who prefer reduced motion.
     */
    video: {
      src: "/work/bmw-x7-drfdaahimv9/video-drp4-eddqge.mp4",
      poster: {
        src: "/work/bmw-x7-drfdaahimv9/poster-drp4-eddqge.jpg",
        alt: { uk: "BMW X7 у студії THE BOX", en: "BMW X7 at THE BOX studio" },
      },
    } as HeroVideo | null,
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
  { label: { uk: "Наші роботи", en: "Our work" }, href: "/portfolio" },
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
