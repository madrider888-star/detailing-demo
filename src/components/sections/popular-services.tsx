import { ArrowIcon, Button } from "@/components/ui/button";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { ServiceCard } from "@/components/cards/service-card";
import { popularServices } from "@/content/services";

export function PopularServices() {
  return (
    <Section id="services" aria-labelledby="popular-title">
      <SectionTitle
        id="popular-title"
        eyebrow="Most requested"
        title="The work owners book most often"
        description="Five programmes cover the majority of what comes through the studio. Each one is quoted after we have seen the car."
        aside={
          <Button href="/services" variant="secondary">
            All services
            <ArrowIcon />
          </Button>
        }
      />

      <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {popularServices.map((service, index) => (
          <Reveal as="li" key={service.slug} delay={index * 60} className="h-full">
            <ServiceCard service={service} className="h-full" priority={index < 3} />
          </Reveal>
        ))}
      </ul>
    </Section>
  );
}
