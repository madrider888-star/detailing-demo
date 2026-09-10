import type { MetadataRoute } from "next";
import { workProjects } from "@/content/work";
import { services } from "@/content/services";
import { site } from "@/content/site";
import { defaultLocale, localePath, locales, localeTag } from "@/lib/i18n";

/**
 * Both language versions of every page, each carrying the full set of
 * `alternates` so search engines pair them up.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();

  const routes = [
    { path: "/", priority: 1 },
    { path: "/services", priority: 0.9 },
    { path: "/portfolio", priority: 0.9 },
    { path: "/about", priority: 0.6 },
    { path: "/contact", priority: 0.8 },
    ...services.map((service) => ({ path: `/services/${service.slug}`, priority: 0.8 })),
    ...workProjects.map((project) => ({ path: `/portfolio/${project.slug}`, priority: 0.7 })),
  ];

  return routes.flatMap((route) =>
    locales.map((locale) => ({
      url: `${site.url}${localePath(route.path, locale)}`,
      lastModified,
      changeFrequency: "monthly" as const,
      priority: route.priority,
      alternates: {
        languages: Object.fromEntries([
          ["x-default", `${site.url}${localePath(route.path, defaultLocale)}`],
          ...locales.map((code) => [localeTag[code], `${site.url}${localePath(route.path, code)}`]),
        ]),
      },
    })),
  );
}
