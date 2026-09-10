import type { Metadata } from "next";
import { site } from "@/content/site";
import { defaultLocale, localePath, locales, localeTag, t, type Locale } from "@/lib/i18n";

interface PageMetaInput {
  locale: Locale;
  title: string;
  description: string;
  /** Locale-free route, e.g. "/services". */
  path: string;
  /**
   * Skip the "%s — THE BOX Detailing" title template. Needed on the home page,
   * whose title already carries the brand.
   */
  absoluteTitle?: boolean;
}

/**
 * Per-page metadata, including the hreflang pair that tells search engines the
 * Ukrainian and English versions of a page are the same document.
 */
export function pageMetadata({
  locale,
  title,
  description,
  path,
  absoluteTitle = false,
}: PageMetaInput): Metadata {
  const canonical = localePath(path, locale);

  const languages: Record<string, string> = { "x-default": localePath(path, defaultLocale) };
  for (const code of locales) languages[localeTag[code]] = localePath(path, code);

  // Avoid "THE BOX Detailing — … — THE BOX Detailing" when the page title is
  // already branded.
  const social = title.includes(site.name) ? title : `${title} — ${site.name}`;

  return {
    title: absoluteTitle ? { absolute: title } : title,
    description,
    alternates: { canonical, languages },
    openGraph: {
      type: "website",
      siteName: site.name,
      locale: localeTag[locale],
      title: social,
      description,
      url: `${site.url}${canonical}`,
    },
    twitter: {
      card: "summary_large_image",
      title: social,
      description,
    },
  };
}

/**
 * LocalBusiness structured data.
 *
 * Only fields the studio has actually confirmed are emitted. Nothing is
 * invented — in particular there is no aggregateRating until real reviews
 * exist, because fabricated review markup breaches Google's guidelines.
 */
export function localBusinessJsonLd(locale: Locale) {
  const address = site.address;

  const data: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "AutoDetailing",
    name: site.name,
    description: t(site.description, locale),
    url: `${site.url}${localePath("/", locale)}`,
    sameAs: [site.instagram.url, ...site.messaging.map((channel) => channel.href)],
  };

  if (site.phone) data.telephone = site.phone;
  if (site.email) data.email = site.email;

  if (address) {
    data.address = {
      "@type": "PostalAddress",
      streetAddress: t(address.street, locale),
      addressLocality: t(address.city, locale),
      ...(address.region ? { addressRegion: t(address.region, locale) } : {}),
      ...(address.postalCode ? { postalCode: address.postalCode } : {}),
      addressCountry: t(address.country, locale),
    };
  }

  return data;
}
