import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { materials } from "@/content/home";

export function Materials() {
  return (
    <Section tone="raised" aria-labelledby="materials-title">
      <SectionTitle
        id="materials-title"
        eyebrow="Materials & equipment"
        title="What we put on your car, and what we use to do it"
        description="Every product is professional-only and every machine is on a maintenance schedule. Nothing here is bought from a shelf."
      />

      <ul className="mt-14 grid gap-px overflow-hidden rounded-2xl outline outline-white/8 sm:grid-cols-2 lg:grid-cols-3">
        {materials.map((item, index) => (
          <Reveal
            as="li"
            key={item.name}
            delay={index * 55}
            className="flex flex-col bg-carbon-900 p-7 outline outline-white/8 sm:p-8"
          >
            <h3 className="font-display text-lg font-medium">{item.name}</h3>
            <p className="mt-3 flex-1 text-[14.5px] leading-relaxed text-mist-400">{item.detail}</p>
            <p className="mt-6 font-display text-[12.5px] tracking-[0.14em] text-brass-500 uppercase">
              {item.spec}
            </p>
          </Reveal>
        ))}
      </ul>
    </Section>
  );
}
