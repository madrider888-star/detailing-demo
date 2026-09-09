import Link from "next/link";
import { Logo } from "@/components/layout/logo";
import { footerNav, site } from "@/content/site";

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-white/8 bg-carbon-950">
      <div className="shell py-16 lg:py-20">
        <div className="grid gap-12 lg:grid-cols-[1.35fr_2fr] lg:gap-20">
          <div>
            <Logo />
            <p className="mt-6 max-w-sm text-[15px] leading-relaxed text-mist-400">
              A paint protection and appearance studio in Odessa. Six climate-controlled bays,
              eleven technicians, and a written record for every car we finish.
            </p>

            <address className="mt-8 space-y-3 text-[15px] not-italic">
              <a
                href={`tel:${site.phoneHref}`}
                className="block font-display text-lg text-mist-100 transition-colors hover:text-brass-400"
              >
                {site.phone}
              </a>
              <a
                href={`mailto:${site.email}`}
                className="block text-mist-300 transition-colors hover:text-mist-100"
              >
                {site.email}
              </a>
              <p className="text-mist-400">
                {site.address.street}
                <br />
                {site.address.city}, {site.address.postalCode}
              </p>
            </address>
          </div>

          <div className="grid gap-10 sm:grid-cols-3">
            {footerNav.map((group) => (
              <nav key={group.title} aria-label={group.title}>
                <h2 className="text-[11px] font-medium tracking-[0.24em] text-mist-500 uppercase">
                  {group.title}
                </h2>
                <ul className="mt-5 space-y-3">
                  {group.items.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className="text-[14.5px] text-mist-300 transition-colors hover:text-mist-100"
                      >
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            ))}
          </div>
        </div>

        <div className="mt-14 grid gap-8 border-t border-white/8 pt-10 sm:grid-cols-2 lg:grid-cols-4">
          {site.hours.map((entry) => (
            <div key={entry.days}>
              <p className="text-[11px] font-medium tracking-[0.2em] text-mist-500 uppercase">
                {entry.days}
              </p>
              <p className="mt-2 font-display text-[15px] text-mist-200">{entry.time}</p>
            </div>
          ))}
          <div className="sm:col-span-2 lg:col-span-1">
            <p className="text-[11px] font-medium tracking-[0.2em] text-mist-500 uppercase">
              Follow
            </p>
            <ul className="mt-2 flex gap-5">
              {site.social.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-[15px] text-mist-300 transition-colors hover:text-mist-100"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-white/8 pt-8 text-[13px] text-mist-500 sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {year} {site.legalName}. Fictional studio — demo project.
          </p>
          <p>
            Prices shown are starting figures and are confirmed after inspection.
          </p>
        </div>
      </div>
    </footer>
  );
}
