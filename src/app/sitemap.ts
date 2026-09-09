import type { MetadataRoute } from "next";
import { services } from "@/content/services";
import { site } from "@/content/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();

  const staticRoutes = [
    { path: "/", priority: 1 },
    { path: "/services", priority: 0.9 },
    { path: "/pricing", priority: 0.8 },
    { path: "/gallery", priority: 0.7 },
    { path: "/about", priority: 0.6 },
    { path: "/contact", priority: 0.8 },
  ].map((route) => ({
    url: `${site.url}${route.path === "/" ? "" : route.path}`,
    lastModified,
    changeFrequency: "monthly" as const,
    priority: route.priority,
  }));

  const serviceRoutes = services.map((service) => ({
    url: `${site.url}/services/${service.slug}`,
    lastModified,
    changeFrequency: "monthly" as const,
    priority: 0.7,
  }));

  return [...staticRoutes, ...serviceRoutes];
}
