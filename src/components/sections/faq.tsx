import { Accordion } from "@/components/ui/accordion";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Button } from "@/components/ui/button";
import type { FaqItem } from "@/types";

interface FaqProps {
  items: FaqItem[];
  eyebrow?: string;
  title?: string;
  description?: string;
  tone?: "base" | "raised";
}

export function Faq({
  items,
  eyebrow = "Questions",
  title = "Answers before you book",
  description,
  tone = "base",
}: FaqProps) {
  return (
    <Section tone={tone} aria-labelledby="faq-title">
      <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
        <div className="lg:sticky lg:top-32 lg:self-start">
          <SectionTitle id="faq-title" eyebrow={eyebrow} title={title} description={description} />
          <div className="mt-8 rounded-2xl border border-white/8 bg-carbon-850 p-6">
            <p className="text-[14.5px] leading-relaxed text-mist-400">
              Not covered here? Send the question with a photo of the car and we will answer it
              properly rather than with a price list.
            </p>
            <Button href="/contact" variant="secondary" size="sm" className="mt-5">
              Ask the studio
            </Button>
          </div>
        </div>
        <Accordion items={items} />
      </div>
    </Section>
  );
}
