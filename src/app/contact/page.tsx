import { BookingForm } from "@/components/forms/booking-form";
import { PageHeader } from "@/components/sections/page-header";
import { Faq } from "@/components/sections/faq";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { Reveal } from "@/components/ui/reveal";
import { getService } from "@/content/services";
import { homeFaq } from "@/content/home";
import { site } from "@/content/site";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Contact & booking",
  description:
    "Book a detailing, coating or paint protection film appointment at Apex Detailing in Odessa. Tell us about the car and we confirm availability within one working day.",
  path: "/contact",
});

interface PageProps {
  searchParams: Promise<{ service?: string }>;
}

export default async function ContactPage({ searchParams }: PageProps) {
  const { service: requested } = await searchParams;
  const preselected = requested && getService(requested) ? requested : "";

  return (
    <>
      <PageHeader
        eyebrow="Contact & booking"
        title="Tell us about the car"
        description="Send the details below and we will come back within one working day with availability and an honest recommendation — including when a cheaper service would do the same job."
        image="/media/service/interior-detailing.svg"
        meta={[
          { label: "Response time", value: "< 1 day" },
          { label: "Assessment", value: "Free" },
          { label: "Collection", value: "Available" },
          { label: "Bays", value: "6" },
        ]}
      />

      <Section aria-labelledby="booking-title">
        <div className="grid gap-14 lg:grid-cols-[1.25fr_0.75fr] lg:gap-20">
          <div>
            <SectionTitle
              id="booking-title"
              eyebrow="Booking request"
              title="Request an appointment"
              description="Nothing is confirmed until we have spoken — this form starts the conversation."
            />
            <div className="mt-12">
              <BookingForm defaultService={preselected} />
            </div>
          </div>

          <Reveal delay={120} className="lg:sticky lg:top-32 lg:self-start">
            <div className="rounded-2xl border border-white/8 bg-carbon-850 p-7 sm:p-8">
              <h2 className="font-display text-lg font-medium">Studio details</h2>

              <dl className="rule mt-6 space-y-5 pt-6">
                <div>
                  <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">Phone</dt>
                  <dd className="mt-1.5">
                    <a
                      href={`tel:${site.phoneHref}`}
                      className="font-display text-lg text-mist-100 transition-colors hover:text-brass-400"
                    >
                      {site.phone}
                    </a>
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">Email</dt>
                  <dd className="mt-1.5">
                    <a
                      href={`mailto:${site.email}`}
                      className="text-[15px] text-mist-200 transition-colors hover:text-brass-400"
                    >
                      {site.email}
                    </a>
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">Address</dt>
                  <dd className="mt-1.5 text-[15px] leading-relaxed text-mist-300">
                    {site.address.street}
                    <br />
                    {site.address.city} {site.address.postalCode}
                    <br />
                    {site.address.country}
                  </dd>
                </div>
              </dl>

              <div className="rule mt-7 pt-6">
                <h3 className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">
                  Opening hours
                </h3>
                <ul className="mt-4 space-y-2.5">
                  {site.hours.map((entry) => (
                    <li
                      key={entry.days}
                      className="flex items-baseline justify-between gap-4 text-[14.5px]"
                    >
                      <span className="text-mist-400">{entry.days}</span>
                      <span className="font-display text-mist-100">{entry.time}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rule mt-7 pt-6">
                <h3 className="text-[11px] tracking-[0.16em] text-mist-500 uppercase">
                  Getting here
                </h3>
                <p className="mt-3 text-[14.5px] leading-relaxed text-mist-400">
                  Bay 3 sits at the rear of the Prymorska courtyard, five minutes from the port.
                  Parking is available directly outside for drop-off.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </Section>

      <Faq items={homeFaq} tone="raised" eyebrow="Before you book" title="Common questions" />
    </>
  );
}
