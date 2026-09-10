import type { Metadata, Viewport } from "next";
import { site } from "@/content/site";
import { ui } from "@/content/ui";
import { localeTag, t, type Locale } from "@/lib/i18n";
import { pageMetadata } from "@/lib/seo";

/** Defaults shared by both root layouts. */
export function rootMetadata(locale: Locale): Metadata {
  return {
    metadataBase: new URL(site.url),
    title: {
      default: `${site.name} — ${t(site.tagline, locale)}`,
      template: `%s — ${site.name}`,
    },
    description: t(site.description, locale),
    applicationName: site.name,
    openGraph: {
      type: "website",
      siteName: site.name,
      locale: localeTag[locale],
      title: `${site.name} — ${t(site.tagline, locale)}`,
      description: t(site.description, locale),
    },
    robots: {
      index: true,
      follow: true,
      googleBot: { index: true, follow: true, "max-image-preview": "large" },
    },
    category: "automotive",
  };
}

export const viewport: Viewport = {
  themeColor: "#050505",
  colorScheme: "dark",
};

export const homeMeta = (locale: Locale) =>
  pageMetadata({
    locale,
    title: `${site.name} — ${t(site.tagline, locale)}`,
    description: t(site.description, locale),
    path: "/",
    absoluteTitle: true,
  });

export const servicesMeta = (locale: Locale) =>
  pageMetadata({
    locale,
    title: t(ui.nav.services, locale),
    description: t(site.description, locale),
    path: "/services",
  });

export const portfolioMeta = (locale: Locale) =>
  pageMetadata({
    locale,
    title: t(ui.nav.portfolio, locale),
    description: t(site.description, locale),
    path: "/portfolio",
  });

export const aboutMeta = (locale: Locale) =>
  pageMetadata({
    locale,
    title: t(ui.nav.about, locale),
    description: t(site.description, locale),
    path: "/about",
  });

export const contactMeta = (locale: Locale) =>
  pageMetadata({
    locale,
    title: t(ui.nav.contact, locale),
    description: t(site.description, locale),
    path: "/contact",
  });
