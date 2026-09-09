import { PricingCard } from "@/components/cards/pricing-card";
import { CTASection } from "@/components/sections/cta-section";
import { Faq } from "@/components/sections/faq";
import { PageHeader } from "@/components/sections/page-header";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { pricingGroups, sizeTiers } from "@/content/pricing";
import { homeFaq } from "@/content/home";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Pricing",
  description:
    "Transparent starting prices for ceramic coating, paint protection film, correction, detailing and window tinting. Vehicle size tiers and studio time included.",
  path: "/pricing",
});

const pricingFaq = [
  {
    question: "Why is every price a 'from' price?",
    answer:
      "Because condition drives cost. Two identical cars can need very different amounts of correction. We quote the exact figure after inspection and it does not move afterwards.",
  },
  {
    question: "How do vehicle size tiers work?",
    answer:
      "Prices listed are for a compact vehicle. Larger vehicles scale by the multipliers in the table above, which reflects surface area and the extra film or product required.",
  },
  {
    question: "Do you take a deposit?",
    answer:
      "For coating and film bookings, yes — 20% to hold the bay, deducted from the final invoice. Detailing services need no deposit.",
  },
  {
    question: "Can services be combined?",
    answer:
      "Yes, and it is usually cheaper. Combining correction with a coating, or film with tinting, saves shared preparation time and we reflect that in the quote.",
  },
];

export default function PricingPage() {
  return (
    <>
      <PageHeader
        eyebrow="Pricing"
        title="What the work costs, before you ask"
        description="Starting prices for every programme we run, grouped by what you are trying to achieve. Final figures are confirmed after a free inspection."
        image="/media/about/materials.svg"
        meta={[
          { label: "Free", value: "Inspection" },
          { label: "Deposit", value: "20%" },
          { label: "Quote validity", value: "30 days" },
          { label: "Payment", value: "On collection" },
        ]}
      />

      <Section aria-labelledby="tiers-title">
        <SectionTitle
          id="tiers-title"
          eyebrow="Vehicle size"
          title="Prices scale with the car, not with the postcode"
          description="Every figure on this page is for a compact vehicle. Larger cars need more product, more film and more hours — here is exactly how that scales."
        />
        <ul className="mt-12 grid gap-px overflow-hidden rounded-2xl outline outline-white/8 sm:grid-cols-2 lg:grid-cols-4">
          {sizeTiers.map((tier, index) => (
            <Reveal
              as="li"
              key={tier.label}
              delay={index * 60}
              className="bg-carbon-850 p-6 outline outline-white/8 sm:p-7"
            >
              <p className="font-display text-[15px] font-medium text-mist-100">{tier.label}</p>
              <p className="mt-2 text-[13.5px] text-mist-500">{tier.example}</p>
              <p className="mt-5 font-display text-2xl font-semibold text-brass-400">
                {tier.multiplier}
              </p>
            </Reveal>
          ))}
        </ul>
      </Section>

      {pricingGroups.map((group, index) => (
        <Section
          key={group.id}
          id={group.id}
          tone={index % 2 === 0 ? "raised" : "base"}
          aria-labelledby={`price-${group.id}`}
        >
          <SectionTitle
            id={`price-${group.id}`}
            eyebrow={`0${index + 1}`}
            title={group.title}
            description={group.description}
          />
          <ul
            className={
              group.options.length === 4
                ? "mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
                : "mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            }
          >
            {group.options.map((option, optionIndex) => (
              <Reveal as="li" key={option.name} delay={optionIndex * 60} className="h-full">
                <PricingCard option={option} className="h-full" />
              </Reveal>
            ))}
          </ul>
        </Section>
      ))}

      <Faq
        items={[...pricingFaq, ...homeFaq.slice(0, 2)]}
        eyebrow="Pricing questions"
        title="How quoting works here"
        tone="raised"
      />

      <CTASection
        eyebrow="Quote"
        title="Get an exact figure for your car"
        description="Send the make, model and a few photos, or bring it in. Either way you get a written quote that holds for thirty days."
        primaryLabel="Request a quote"
        secondaryLabel="Browse services"
      />
    </>
  );
}
