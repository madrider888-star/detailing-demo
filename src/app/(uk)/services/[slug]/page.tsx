import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getService, services } from "@/content/services";
import { ServiceDetailView } from "@/views/service-detail-view";
import { t } from "@/lib/i18n";
import { pageMetadata } from "@/lib/seo";

const locale = "uk" as const;

export function generateStaticParams() {
  return services.map((service) => ({ slug: service.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const service = getService(slug);
  if (!service) return {};

  return pageMetadata({
    locale,
    title: t(service.title, locale),
    description: t(service.summary, locale),
    path: `/services/${service.slug}`,
  });
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const service = getService(slug);
  if (!service) notFound();

  return <ServiceDetailView service={service} locale={locale} />;
}
