import { BookingForm } from "@/components/forms/booking-form";
import { FaqSection } from "@/components/sections/faq-section";
import { PageHeader } from "@/components/sections/page-header";
import { ArrowIcon } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { hasContactDetails, site } from "@/content/site";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";

export function ContactView({
  locale,
  defaultService = "",
  defaultMessage = "",
}: {
  locale: Locale;
  defaultService?: string;
  defaultMessage?: string;
}) {
  const address = site.address;

  return (
    <>
      <PageHeader
        locale={locale}
        eyebrow={t(ui.sections.contactEyebrow, locale)}
        title={t(ui.sections.contactTitle, locale)}
      />

      <Section aria-labelledby="booking-title">
        <div className="grid gap-14 lg:grid-cols-[1.2fr_0.8fr] lg:gap-20">
          <div>
            <SectionTitle
              id="booking-title"
              eyebrow={t(ui.sections.contactEyebrow, locale)}
              title={t(ui.form.heading, locale)}
            />
            <div className="mt-12">
              <BookingForm locale={locale} defaultService={defaultService} defaultMessage={defaultMessage} />
            </div>
          </div>

          <Reveal delay={120} className="lg:sticky lg:top-32 lg:self-start">
            <div className="rounded-card border border-line bg-ink-850 p-7 sm:p-8">
              <h2 className="font-display text-lg font-medium uppercase">
                {t(ui.sections.contactEyebrow, locale)}
              </h2>

              {site.phone || site.email || address ? (
                <dl className="rule mt-6 space-y-5 pt-6">
                  {site.phone ? (
                    <div>
                      <dt className="text-[10px] tracking-[0.2em] text-chalk-500 uppercase">
                        {t(ui.labels.phone, locale)}
                      </dt>
                      <dd className="mt-1.5">
                        <a
                          href={`tel:${site.phone.replace(/\s/g, "")}`}
                          className="font-display text-lg text-chalk-50 transition-colors hover:text-accent"
                        >
                          {site.phone}
                        </a>
                      </dd>
                    </div>
                  ) : null}

                  {site.email ? (
                    <div>
                      <dt className="text-[10px] tracking-[0.2em] text-chalk-500 uppercase">
                        {t(ui.labels.email, locale)}
                      </dt>
                      <dd className="mt-1.5">
                        <a
                          href={`mailto:${site.email}`}
                          className="text-[15px] text-chalk-200 transition-colors hover:text-accent"
                        >
                          {site.email}
                        </a>
                      </dd>
                    </div>
                  ) : null}

                  {address ? (
                    <div>
                      <dt className="text-[10px] tracking-[0.2em] text-chalk-500 uppercase">
                        {t(ui.labels.address, locale)}
                      </dt>
                      <dd className="mt-1.5 text-[15px] leading-relaxed text-chalk-300">
                        {t(address.street, locale)}
                        <br />
                        {t(address.city, locale)}
                        {address.postalCode ? `, ${address.postalCode}` : ""}
                        {address.mapUrl ? (
                          <>
                            <br />
                            <a
                              href={address.mapUrl}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="mt-2 inline-block text-accent underline underline-offset-4"
                            >
                              {locale === "uk"
                                ? "Прокласти маршрут"
                                : "Get directions"}
                            </a>
                          </>
                        ) : null}
                      </dd>
                    </div>
                  ) : null}
                </dl>
              ) : null}

              <div className="rule mt-7 pt-6">
                <h3 className="text-[10px] tracking-[0.2em] text-chalk-500 uppercase">
                  {t(ui.labels.follow, locale)}
                </h3>
                <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-3">
                  <li>
                    <a
                      href={site.instagram.url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="inline-flex items-center gap-2 text-[15px] text-chalk-200 transition-colors hover:text-accent"
                    >
                      <Icon name="instagram" className="h-4 w-4" />
                      {site.instagram.handle}
                    </a>
                  </li>
                  {site.messaging.map((channel) => (
                    <li key={channel.href}>
                      <a
                        href={channel.href}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="group inline-flex items-center gap-2 text-[15px] text-chalk-200 transition-colors hover:text-accent"
                      >
                        <Icon name={channel.icon} className="h-4 w-4" />
                        {channel.label}
                        <ArrowIcon className="transition-transform duration-300 group-hover:translate-x-1" />
                      </a>
                    </li>
                  ))}
                </ul>
              </div>

              {site.hours.length > 0 ? (
                <div className="rule mt-7 pt-6">
                  <h3 className="text-[10px] tracking-[0.2em] text-chalk-500 uppercase">
                    {t(ui.labels.openingHours, locale)}
                  </h3>
                  <ul className="mt-4 space-y-2.5">
                    {site.hours.map((entry) => (
                      <li
                        key={t(entry.days, locale)}
                        className="flex items-baseline justify-between gap-4 text-[14.5px]"
                      >
                        <span className="text-chalk-400">
                          {t(entry.days, locale)}
                        </span>
                        <span className="font-display text-chalk-50">
                          {t(entry.time, locale)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {!hasContactDetails() ? (
                <p className="mt-6 text-[13px] leading-relaxed text-chalk-500">
                  {locale === "uk"
                    ? "Контактні дані додамо після підтвердження студією."
                    : "Contact details will appear once the studio confirms them."}
                </p>
              ) : null}
            </div>
          </Reveal>
        </div>
      </Section>

      <FaqSection locale={locale} />
    </>
  );
}
