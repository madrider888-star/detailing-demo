import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { TestimonialCard } from "@/components/cards/testimonial-card";
import { testimonials } from "@/content/testimonials";

export function Testimonials() {
  return (
    <Section tone="raised" aria-labelledby="reviews-title">
      <SectionTitle
        id="reviews-title"
        eyebrow="Owners"
        title="What people say after collection"
        description="Reviews from owners who let us keep their car for a week — the ones who saw the work up close."
        aside={
          <div className="flex items-center gap-5 rounded-2xl border border-white/8 bg-carbon-850 px-6 py-5">
            <span className="font-display text-4xl font-semibold text-mist-100">4.9</span>
            <span className="text-[13px] leading-snug text-mist-400">
              Average rating
              <br />
              over 318 reviews
            </span>
          </div>
        }
      />

      <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {testimonials.map((testimonial, index) => (
          <Reveal as="li" key={testimonial.author} delay={index * 60} className="h-full">
            <TestimonialCard testimonial={testimonial} />
          </Reveal>
        ))}
      </ul>
    </Section>
  );
}
