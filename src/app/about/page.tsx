import Image from "next/image";
import { CTASection } from "@/components/sections/cta-section";
import { PageHeader } from "@/components/sections/page-header";
import { Testimonials } from "@/components/sections/testimonials";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { equipment, products, story, values } from "@/content/about";
import { site } from "@/content/site";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "About the studio",
  description:
    "Apex Detailing has protected and restored vehicles in Odessa since 2014. Six climate-controlled bays, eleven technicians, and a documented process for every car.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <>
      <PageHeader
        eyebrow="The studio"
        title="Eleven years of doing the unglamorous half properly"
        description="Apex started as two people and one lift on Prymorska Street. What has not changed is the rule we opened with: we would rather turn work away than rush a correction."
        image="/media/about/bay.svg"
        meta={site.stats.map((stat) => ({ label: stat.label, value: stat.value }))}
      />

      <Section aria-labelledby="story-title">
        <div className="grid gap-14 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
          <div className="lg:sticky lg:top-32 lg:self-start">
            <SectionTitle
              id="story-title"
              eyebrow="Story"
              title="How the studio got here"
              description="Growth was slow on purpose. Every expansion followed the training, not the other way round."
            />
          </div>

          <ol className="relative">
            <span
              aria-hidden="true"
              className="absolute top-3 bottom-3 left-[7px] w-px bg-gradient-to-b from-brass-600/50 via-white/10 to-transparent"
            />
            {story.map((entry, index) => (
              <Reveal
                as="li"
                key={entry.year}
                delay={index * 70}
                className="relative grid grid-cols-[16px_1fr] gap-x-6 pb-12 last:pb-0"
              >
                <span className="relative z-10 mt-2 h-3.5 w-3.5 rounded-full border border-brass-500/50 bg-carbon-950" />
                <div>
                  <p className="font-display text-[13px] font-medium tracking-[0.2em] text-brass-500">
                    {entry.year}
                  </p>
                  <h3 className="mt-3 font-display text-xl font-medium">{entry.title}</h3>
                  <p className="mt-3 max-w-2xl text-[15.5px] leading-relaxed text-mist-400">
                    {entry.description}
                  </p>
                </div>
              </Reveal>
            ))}
          </ol>
        </div>
      </Section>

      <Section tone="raised" aria-labelledby="values-title">
        <SectionTitle
          id="values-title"
          eyebrow="Values"
          title="Four rules we do not bend"
          description="They cost us work occasionally. They are also the reason most of our bookings come from someone who has already been here."
        />
        <ul className="mt-14 grid gap-px overflow-hidden rounded-2xl outline outline-white/8 sm:grid-cols-2">
          {values.map((value, index) => (
            <Reveal
              as="li"
              key={value.title}
              delay={index * 60}
              className="bg-carbon-900 p-7 outline outline-white/8 sm:p-9"
            >
              <span className="font-display text-[13px] font-medium tracking-[0.2em] text-brass-500">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-5 font-display text-xl font-medium">{value.title}</h3>
              <p className="mt-3 text-[15px] leading-relaxed text-mist-400">{value.description}</p>
            </Reveal>
          ))}
        </ul>
      </Section>

      <Section aria-labelledby="equipment-title">
        <div className="grid gap-14 lg:grid-cols-2 lg:gap-16">
          <div>
            <SectionTitle
              id="equipment-title"
              eyebrow="Equipment"
              title="The workshop was built around the work"
            />
            <ul className="mt-10 divide-y divide-white/8 border-y border-white/8">
              {equipment.map((item) => (
                <li key={item.name} className="py-5">
                  <p className="font-display text-[16px] font-medium text-mist-100">{item.name}</p>
                  <p className="mt-1.5 text-[14.5px] leading-relaxed text-mist-400">
                    {item.detail}
                  </p>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <SectionTitle
              eyebrow="Products"
              title="Professional-only, and traceable per vehicle"
            />
            <ul className="mt-10 divide-y divide-white/8 border-y border-white/8">
              {products.map((item) => (
                <li key={item.brand} className="py-5">
                  <p className="font-display text-[16px] font-medium text-mist-100">{item.brand}</p>
                  <p className="mt-1.5 text-[14.5px] leading-relaxed text-mist-400">
                    {item.detail}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Reveal delay={120} className="mt-16">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/8">
              <Image
                src="/media/about/craft.svg"
                alt="Split panel showing swirl-marked clear coat next to a corrected finish"
                fill
                sizes="(min-width: 640px) 50vw, 100vw"
                className="object-cover"
              />
            </div>
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/8">
              <Image
                src="/media/about/materials.svg"
                alt="Water beading on a freshly coated panel"
                fill
                sizes="(min-width: 640px) 50vw, 100vw"
                className="object-cover"
              />
            </div>
          </div>
        </Reveal>
      </Section>

      <Section tone="raised" aria-labelledby="philosophy-title">
        <div className="mx-auto max-w-3xl text-center">
          <p className="eyebrow justify-center">
            <span aria-hidden="true" className="h-px w-8 bg-brass-600/70" />
            Philosophy
          </p>
          <blockquote className="mt-8">
            <p className="font-display text-2xl leading-snug font-medium text-mist-100 sm:text-3xl lg:text-[2.25rem]">
              &ldquo;A finish is not something you apply. It is what is left after every shortcut has
              been refused.&rdquo;
            </p>
          </blockquote>
          <p className="mt-8 text-[14px] tracking-[0.14em] text-mist-500 uppercase">
            Studio principle, since 2014
          </p>
        </div>
      </Section>

      <Testimonials />

      <CTASection
        eyebrow="Visit"
        title="Come and see the bays"
        description="We are on Prymorska Street, five minutes from the port. Drop in during opening hours or book an assessment and we will hold a bay for you."
        primaryLabel="Book an assessment"
        secondaryLabel="Contact the studio"
        secondaryHref="/contact"
      />
    </>
  );
}
