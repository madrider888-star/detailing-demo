import Image from "next/image";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { SpecList } from "@/components/ui/spec-list";
import { Reveal } from "@/components/ui/reveal";
import { Accordion } from "@/components/ui/accordion";
import { PageHeader } from "@/components/sections/page-header";
import { ProcessSteps } from "@/components/sections/process-steps";
import { ServiceCard } from "@/components/cards/service-card";
import { CTASection } from "@/components/sections/cta-section";
import { categoryLabels, getRelatedServices, getService, services } from "@/content/services";
import { site } from "@/content/site";
import { formatPrice } from "@/lib/utils";
import { pageMetadata } from "@/lib/seo";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return services.map((service) => ({ slug: service.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const service = getService(slug);

  if (!service) {
    return pageMetadata({
      title: "Service not found",
      description: "This service is not part of the Apex Detailing programme.",
      path: `/services/${slug}`,
    });
  }

  return pageMetadata({
    title: service.title,
    description: `${service.summary} From ${formatPrice(service.priceFrom)}, ${service.duration} in the studio at ${site.name}, ${site.address.city}.`,
    path: `/services/${service.slug}`,
  });
}

export default async function ServiceDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const service = getService(slug);

  if (!service) notFound();

  const related = getRelatedServices(service.slug);
  const bookingHref = `/contact?service=${service.slug}`;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: service.title,
    serviceType: categoryLabels[service.category],
    description: service.summary,
    provider: { "@type": "AutoDetailing", name: site.legalName, telephone: site.phone },
    areaServed: site.address.city,
    offers: {
      "@type": "Offer",
      price: service.priceFrom,
      priceCurrency: "USD",
      availability: "https://schema.org/InStock",
    },
  };

  return (
    <>
      <PageHeader
        eyebrow={service.tagline}
        title={service.title}
        description={service.summary}
        image={service.image}
        crumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: service.title, href: `/services/${service.slug}` },
        ]}
        meta={[
          { label: "From", value: formatPrice(service.priceFrom) },
          { label: "Studio time", value: service.duration },
          { label: "Category", value: categoryLabels[service.category] },
          { label: "Warranty", value: service.warranty ?? "Job-specific" },
        ]}
      >
        <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
          <Button href={bookingHref} size="lg">
            Book {service.title}
            <ArrowIcon />
          </Button>
          <Button href="/pricing" variant="secondary" size="lg">
            See full pricing
          </Button>
        </div>
      </PageHeader>

      <Section aria-labelledby="overview-title">
        <div className="grid gap-14 lg:grid-cols-[1.15fr_0.85fr] lg:gap-20">
          <div>
            <SectionTitle
              id="overview-title"
              eyebrow="Overview"
              title={`What ${service.title.toLowerCase()} actually does`}
            />
            <div className="mt-8 space-y-5">
              {service.intro.map((paragraph) => (
                <p key={paragraph} className="text-[16.5px] leading-relaxed text-mist-300">
                  {paragraph}
                </p>
              ))}
            </div>

            <ul className="mt-10 flex flex-wrap gap-2">
              {service.highlights.map((highlight) => (
                <li key={highlight}>
                  <Badge>{highlight}</Badge>
                </li>
              ))}
            </ul>
          </div>

          <Reveal delay={120}>
            <aside className="rounded-2xl border border-white/8 bg-carbon-850 p-7 sm:p-8 lg:sticky lg:top-32">
              <h2 className="font-display text-lg font-medium">What is included</h2>
              <SpecList items={service.includes} dense className="mt-6" />

              <dl className="rule mt-7 grid grid-cols-2 gap-6 pt-6">
                <div>
                  <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">
                    Starting price
                  </dt>
                  <dd className="mt-1.5 font-display text-2xl font-semibold text-mist-100">
                    {formatPrice(service.priceFrom)}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">
                    Estimated duration
                  </dt>
                  <dd className="mt-1.5 font-display text-2xl font-semibold text-mist-100">
                    {service.duration}
                  </dd>
                </div>
              </dl>

              {service.warranty ? (
                <p className="mt-5 text-[13px] text-brass-500">Warranty: {service.warranty}</p>
              ) : null}

              <Button href={bookingHref} className="mt-7 w-full">
                Book this service
              </Button>
              <p className="mt-4 text-center text-[12.5px] text-mist-500">
                Final price confirmed after inspection.
              </p>
            </aside>
          </Reveal>
        </div>
      </Section>

      <Section tone="raised" aria-labelledby="benefits-title">
        <SectionTitle
          id="benefits-title"
          eyebrow="Benefits"
          title="Why owners choose it"
          description={`What ${service.title.toLowerCase()} changes about living with the car day to day.`}
        />
        <ul className="mt-14 grid gap-px overflow-hidden rounded-2xl outline outline-white/8 sm:grid-cols-2">
          {service.benefits.map((benefit, index) => (
            <Reveal
              as="li"
              key={benefit.title}
              delay={index * 60}
              className="bg-carbon-900 p-7 outline outline-white/8 sm:p-9"
            >
              <h3 className="font-display text-lg font-medium">{benefit.title}</h3>
              <p className="mt-3 text-[15px] leading-relaxed text-mist-400">
                {benefit.description}
              </p>
            </Reveal>
          ))}
        </ul>
      </Section>

      <Section aria-labelledby="service-process-title">
        <div className="grid gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
          <div className="lg:sticky lg:top-32 lg:self-start">
            <SectionTitle
              id="service-process-title"
              eyebrow="Process"
              title="How the job runs"
              description={`Total studio time is ${service.duration}. Each stage is signed off before the next one starts.`}
            />
            <div className="relative mt-10 aspect-[4/3] overflow-hidden rounded-2xl border border-white/8">
              <Image
                src={service.image}
                alt={`${service.title} in progress at ${site.name}`}
                fill
                sizes="(min-width: 1024px) 460px, 100vw"
                className="object-cover"
              />
              <div
                aria-hidden="true"
                className="absolute inset-0 bg-gradient-to-t from-carbon-950/70 to-transparent"
              />
            </div>
          </div>
          <ProcessSteps steps={service.process} />
        </div>
      </Section>

      <Section tone="raised" aria-labelledby="service-faq-title">
        <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
          <div className="lg:sticky lg:top-32 lg:self-start">
            <SectionTitle
              id="service-faq-title"
              eyebrow="Questions"
              title={`${service.title}, answered`}
            />
          </div>
          <Accordion items={service.faq} />
        </div>
      </Section>

      <Section aria-labelledby="related-title">
        <SectionTitle
          id="related-title"
          eyebrow="Also consider"
          title="Services that pair with this one"
          aside={
            <Button href="/services" variant="secondary">
              All services
              <ArrowIcon />
            </Button>
          }
        />
        <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {related.map((item, index) => (
            <Reveal as="li" key={item.slug} delay={index * 60} className="h-full">
              <ServiceCard service={item} className="h-full" />
            </Reveal>
          ))}
        </ul>
      </Section>

      <CTASection
        eyebrow="Book"
        title={`Reserve a bay for ${service.title.toLowerCase()}`}
        description={`Starting at ${formatPrice(service.priceFrom)} with ${service.duration} in the studio. Send the car's details and we will confirm a date within one working day.`}
        primaryHref={bookingHref}
        primaryLabel="Book Detailing"
      />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </>
  );
}
