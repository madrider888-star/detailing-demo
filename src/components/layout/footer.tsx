import Link from "next/link";
import { Logo } from "@/components/layout/logo";
import { Icon } from "@/components/ui/icon";
import { mainNav, site } from "@/content/site";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";

export function Footer({ locale }: { locale: Locale }) {
  const year = new Date().getFullYear();
  const address = site.address;

  return (
    <footer className="border-t border-line bg-ink-950">
      <div className="shell py-16 lg:py-20">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_1fr_1fr] lg:gap-16">
          <div>
            <Logo locale={locale} />
            <p className="mt-6 max-w-sm text-[15px] leading-relaxed text-chalk-400">
              {t(site.description, locale)}
            </p>

            <ul className="mt-8 flex flex-wrap gap-x-5 gap-y-3">
              <li>
                <a
                  href={site.instagram.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-2 text-[14px] text-chalk-300 transition-colors hover:text-accent"
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
                    className="inline-flex items-center gap-2 text-[14px] text-chalk-300 transition-colors hover:text-accent"
                  >
                    <Icon name={channel.icon} className="h-4 w-4" />
                    {channel.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <nav aria-label="Footer">
            <h2 className="text-[10px] font-medium tracking-[0.24em] text-chalk-500 uppercase">
              {t(ui.nav.home, locale)}
            </h2>
            <ul className="mt-5 space-y-3">
              {mainNav.map((item) => (
                <li key={item.href}>
                  <Link
                    href={localePath(item.href, locale)}
                    className="text-[14.5px] text-chalk-300 transition-colors hover:text-accent"
                  >
                    {t(item.label, locale)}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {site.phone || site.email || address || site.hours.length > 0 ? (
            <div>
              <h2 className="text-[10px] font-medium tracking-[0.24em] text-chalk-500 uppercase">
                {t(ui.sections.contactEyebrow, locale)}
              </h2>
              <address className="mt-5 space-y-3 text-[15px] not-italic">
                {site.phone ? (
                  <a
                    href={`tel:${site.phone.replace(/\s/g, "")}`}
                    className="block font-display text-lg text-chalk-50 transition-colors hover:text-accent"
                  >
                    {site.phone}
                  </a>
                ) : null}
                {site.email ? (
                  <a
                    href={`mailto:${site.email}`}
                    className="block text-chalk-300 transition-colors hover:text-accent"
                  >
                    {site.email}
                  </a>
                ) : null}
                {address ? (
                  <p className="text-chalk-400">
                    {t(address.street, locale)}
                    <br />
                    {t(address.city, locale)}
                    {address.postalCode ? `, ${address.postalCode}` : ""}
                  </p>
                ) : null}
              </address>

              {site.hours.length > 0 ? (
                <ul className="mt-6 space-y-2">
                  {site.hours.map((entry) => (
                    <li
                      key={t(entry.days, locale)}
                      className="flex items-baseline justify-between gap-4 text-[14px]"
                    >
                      <span className="text-chalk-400">
                        {t(entry.days, locale)}
                      </span>
                      <span className="text-chalk-100">
                        {t(entry.time, locale)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="mt-14 border-t border-line pt-8 text-[13px] text-chalk-500">
          <p>
            © {year} {site.name}. {t(ui.footer.rights, locale)}
          </p>
        </div>
      </div>
    </footer>
  );
}
