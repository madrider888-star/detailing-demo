import Image from "next/image";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { differentiators } from "@/content/home";

export function WhyChooseUs() {
  return (
    <Section aria-labelledby="why-title">
      <div className="grid gap-14 lg:grid-cols-[1fr_1.05fr] lg:gap-20">
        <div>
          <SectionTitle
            id="why-title"
            eyebrow="Why Apex"
            title="A studio built around the boring parts"
            description="Anyone can apply a coating. The result comes from measurement, environment and the discipline to stop at the right moment."
          />

          <Reveal delay={120} className="mt-12">
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/8">
              <Image
                src="/media/about/bay.svg"
                alt="A vehicle under inspection lighting in one of the studio's climate-controlled bays"
                fill
                sizes="(min-width: 1024px) 520px, 100vw"
                className="object-cover"
              />
              <div
                aria-hidden="true"
                className="absolute inset-0 bg-gradient-to-t from-carbon-950/70 to-transparent"
              />
              <p className="absolute bottom-5 left-6 text-[12px] tracking-[0.18em] text-mist-300 uppercase">
                Bay 3 · Inspection lighting
              </p>
            </div>
          </Reveal>
        </div>

        <ul className="grid gap-px self-start overflow-hidden rounded-2xl outline outline-white/8">
          {differentiators.map((item, index) => (
            <Reveal
              as="li"
              key={item.title}
              delay={index * 70}
              className="bg-carbon-850 p-7 outline outline-white/8 sm:p-9"
            >
              <div className="flex items-baseline justify-between gap-6">
                <h3 className="font-display text-xl font-medium">{item.title}</h3>
                <span className="font-display text-[13px] font-medium text-brass-500">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>
              <p className="mt-3.5 text-[15px] leading-relaxed text-mist-400">{item.description}</p>
              <p className="mt-5 text-[12px] tracking-[0.16em] text-mist-500 uppercase">
                {item.metric}
              </p>
            </Reveal>
          ))}
        </ul>
      </div>
    </Section>
  );
}
