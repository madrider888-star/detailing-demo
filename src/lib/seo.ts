import type { Metadata } from "next";
import { site } from "@/content/site";

interface PageMetaInput {
  title: string;
  description: string;
  /** Route path beginning with a slash, e.g. "/services". */
  path: string;
}

/**
 * Builds per-route metadata on top of the defaults declared in the root layout.
 * Keeping this in one place stops canonical URLs and card copy drifting apart.
 */
export function pageMetadata({ title, description, path }: PageMetaInput): Metadata {
  const url = `${site.url}${path === "/" ? "" : path}`;
  // Avoid "Apex Detailing — Apex Detailing" when the page title is already branded.
  const social = title.includes(site.name) ? title : `${title} — ${site.name}`;

  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: {
      type: "website",
      siteName: site.name,
      locale: site.locale,
      title: social,
      description,
      url,
    },
    twitter: {
      card: "summary_large_image",
      title: social,
      description,
    },
  };
}

/** LocalBusiness structured data rendered once, in the root layout. */
export function localBusinessJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "AutoDetailing",
    name: site.legalName,
    description: site.description,
    url: site.url,
    telephone: site.phone,
    email: site.email,
    image: `${site.url}/opengraph-image`,
    priceRange: "$$$",
    address: {
      "@type": "PostalAddress",
      streetAddress: site.address.street,
      addressLocality: site.address.city,
      addressRegion: site.address.region,
      postalCode: site.address.postalCode,
      addressCountry: "UA",
    },
    openingHoursSpecification: [
      {
        "@type": "OpeningHoursSpecification",
        dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        opens: "09:00",
        closes: "20:00",
      },
      {
        "@type": "OpeningHoursSpecification",
        dayOfWeek: ["Saturday"],
        opens: "10:00",
        closes: "18:00",
      },
    ],
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: "4.9",
      reviewCount: "318",
    },
  };
}
