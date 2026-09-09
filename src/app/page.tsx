import { Hero } from "@/components/sections/hero";
import { PopularServices } from "@/components/sections/popular-services";
import { ComparisonShowcase } from "@/components/sections/comparison-showcase";
import { WhyChooseUs } from "@/components/sections/why-choose-us";
import { Materials } from "@/components/sections/materials";
import { ProcessSteps } from "@/components/sections/process-steps";
import { Testimonials } from "@/components/sections/testimonials";
import { Faq } from "@/components/sections/faq";
import { CTASection } from "@/components/sections/cta-section";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { comparisons, homeFaq, studioProcess } from "@/content/home";
import { pageMetadata } from "@/lib/seo";
import { site } from "@/content/site";

export const metadata = pageMetadata({
  // The root layout's title template does not apply to its own segment, so the
  // home page carries the brand itself.
  title: `${site.name} — ${site.tagline} in ${site.address.city}`,
  description: site.description,
  path: "/",
});

export default function HomePage() {
  return (
    <>
      <Hero />
      <PopularServices />

      <Section tone="raised" aria-labelledby="compare-title">
        <SectionTitle
          id="compare-title"
          eyebrow="Before / After"
          title="The difference is measurable, not marketing"
          description="Three cars that came in with paint the owners had given up on. Drag the handle to see what came off and what came back."
        />
        <div className="mt-14">
          <ComparisonShowcase pairs={comparisons} />
        </div>
      </Section>

      <WhyChooseUs />
      <Materials />

      <Section aria-labelledby="process-title">
        <div className="grid gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
          <div className="lg:sticky lg:top-32 lg:self-start">
            <SectionTitle
              id="process-title"
              eyebrow="Process"
              title="Six days, and you know what happens on each"
              description="Timelines vary by service, but the sequence never does. You approve a written scope before any work begins."
            />
          </div>
          <ProcessSteps steps={studioProcess} />
        </div>
      </Section>

      <Testimonials />
      <Faq items={homeFaq} />
      <CTASection />
    </>
  );
}
