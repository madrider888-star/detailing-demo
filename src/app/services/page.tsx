import { ServiceCard } from "@/components/cards/service-card";
import { CTASection } from "@/components/sections/cta-section";
import { Faq } from "@/components/sections/faq";
import { PageHeader } from "@/components/sections/page-header";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { categoryLabels, services } from "@/content/services";
import { homeFaq } from "@/content/home";
import type { ServiceCategory } from "@/types";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Services",
  description:
    "Ceramic coating, paint protection film, paint correction, interior and exterior detailing, window tinting and wheel protection — with starting prices and studio time for each.",
  path: "/services",
});

const order: ServiceCategory[] = [
  "protection",
  "ppf",
  "correction",
  "exterior",
  "interior",
  "tinting",
];

export default function ServicesPage() {
  const grouped = order
    .map((category) => ({
      category,
      items: services.filter((service) => service.category === category),
    }))
    .filter((group) => group.items.length > 0);

  return (
    <>
      <PageHeader
        eyebrow="Services"
        title="Twelve programmes, one standard of preparation"
        description="Every service below starts with the same decontamination and assessment. What changes is how far we take the finish and what we leave protecting it."
        image="/media/service/full-body-ppf.svg"
      />

      {grouped.map((group, groupIndex) => (
        <Section
          key={group.category}
          tone={groupIndex % 2 === 1 ? "raised" : "base"}
          aria-labelledby={`group-${group.category}`}
        >
          <SectionTitle
            id={`group-${group.category}`}
            eyebrow={`0${groupIndex + 1}`}
            title={categoryLabels[group.category]}
            description={groupDescriptions[group.category]}
          />
          <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {group.items.map((service, index) => (
              <Reveal as="li" key={service.slug} delay={index * 55} className="h-full">
                <ServiceCard
                  service={service}
                  className="h-full"
                  priority={groupIndex === 0 && index < 2}
                />
              </Reveal>
            ))}
          </ul>
        </Section>
      ))}

      <Faq items={homeFaq.slice(0, 4)} tone="raised" title="Booking questions" />
      <CTASection
        title="Not sure which service the car needs?"
        description="Bring it in. We will look at it under proper lighting, tell you what it actually needs, and put a written scope in your hand before you decide anything."
        primaryLabel="Book an assessment"
        secondaryLabel="See pricing"
        secondaryHref="/pricing"
      />
    </>
  );
}

const groupDescriptions: Record<ServiceCategory, string> = {
  protection:
    "Semi-permanent coatings that harden the surface and change how the car behaves in the wash.",
  ppf: "Urethane film that takes the physical damage so the paint underneath never does.",
  correction: "Machine polishing to a measured target, with the clear coat depth known before we start.",
  exterior: "Wash, decontamination and presentation work — the maintenance layer between bigger jobs.",
  interior: "Cabin restoration and surface protection, done with the chemistry each material needs.",
  tinting: "Nano-ceramic window film for heat, glare and UV, cut and installed in a filtered bay.",
};
