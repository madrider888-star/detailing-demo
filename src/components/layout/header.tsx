"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/layout/logo";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { mainNav, site } from "@/content/site";
import { ui } from "@/content/ui";
import { localePath, stripLocale, t, type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function Header({ locale }: { locale: Locale }) {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [lastPath, setLastPath] = useState(pathname);

  // Close the drawer on navigation without an extra effect pass.
  if (lastPath !== pathname) {
    setLastPath(pathname);
    setMenuOpen(false);
  }

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  const currentBase = stripLocale(pathname);
  const isActive = (href: string) =>
    currentBase === href || (href !== "/" && currentBase.startsWith(`${href}/`));

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-500",
        scrolled || menuOpen ? "glass border-b border-line" : "border-b border-transparent",
      )}
    >
      <div className="shell flex h-16 items-center justify-between gap-6 sm:h-20">
        <Logo locale={locale} />

        <nav aria-label="Primary" className="hidden lg:block">
          <ul className="flex items-center gap-8">
            {mainNav.map((item) => (
              <li key={item.href}>
                <Link
                  href={localePath(item.href, locale)}
                  aria-current={isActive(item.href) ? "page" : undefined}
                  className={cn(
                    "relative py-2 text-[12px] font-medium tracking-[0.16em] uppercase transition-colors duration-300",
                    isActive(item.href) ? "text-accent" : "text-chalk-300 hover:text-chalk-50",
                  )}
                >
                  {t(item.label, locale)}
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute inset-x-0 -bottom-0.5 h-px origin-left bg-accent transition-transform duration-300",
                      isActive(item.href) ? "scale-x-100" : "scale-x-0",
                    )}
                  />
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="hidden items-center gap-6 lg:flex">
          <LanguageSwitcher locale={locale} />
          {site.phone ? (
            <a
              href={`tel:${site.phone.replace(/\s/g, "")}`}
              className="text-[13px] font-medium text-chalk-200 transition-colors hover:text-accent"
            >
              {site.phone}
            </a>
          ) : null}
          {/* Messenger icons next to the phone: one tap opens a direct chat. */}
          {site.messaging.map((channel) => (
            <a
              key={channel.href}
              href={channel.href}
              target="_blank"
              rel="noreferrer noopener"
              aria-label={channel.label}
              title={channel.label}
              className="-mx-2 grid h-10 w-10 place-items-center rounded-button border border-line text-chalk-100 transition-colors hover:border-accent hover:text-accent"
            >
              <Icon name={channel.icon} className="h-[18px] w-[18px]" />
            </a>
          ))}
          <Button href={localePath("/contact", locale)} size="sm">
            {t(ui.actions.book, locale)}
          </Button>
        </div>

        <div className="flex items-center gap-3 lg:hidden">
          <LanguageSwitcher locale={locale} />
          {site.messaging[0] ? (
            <a
              href={site.messaging[0].href}
              target="_blank"
              rel="noreferrer noopener"
              aria-label={site.messaging[0].label}
              className="grid h-11 w-11 place-items-center text-chalk-100 transition-colors hover:text-accent"
            >
              <Icon name={site.messaging[0].icon} className="h-[22px] w-[22px]" />
            </a>
          ) : null}
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-controls="mobile-navigation"
            className="-mr-2 grid h-11 w-11 place-items-center text-chalk-100 transition-colors hover:text-accent"
          >
            <span className="sr-only">
              {t(menuOpen ? ui.nav.menuClose : ui.nav.menuOpen, locale)}
            </span>
            <Icon name={menuOpen ? "close" : "menu"} className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* Solid panel: a backdrop filter nested inside the header's own filter
          does not composite, which would leave the page readable through it. */}
      <div
        id="mobile-navigation"
        hidden={!menuOpen}
        className="fixed inset-x-0 top-16 bottom-0 overflow-y-auto overscroll-contain border-t border-line bg-ink-950 sm:top-20 lg:hidden"
      >
        <nav aria-label="Mobile" className="shell py-8">
          <ul className="flex flex-col">
            {mainNav.map((item) => (
              <li key={item.href} className="border-b border-line last:border-0">
                <Link
                  href={localePath(item.href, locale)}
                  aria-current={isActive(item.href) ? "page" : undefined}
                  className={cn(
                    "flex items-center justify-between py-5 font-display text-2xl font-semibold uppercase transition-colors",
                    isActive(item.href) ? "text-accent" : "text-chalk-50",
                  )}
                >
                  {t(item.label, locale)}
                  <Icon name="arrow" className="h-5 w-5 text-chalk-500" />
                </Link>
              </li>
            ))}
          </ul>

          <div className="mt-10 flex flex-col gap-3">
            <Button href={localePath("/contact", locale)} size="lg">
              {t(ui.actions.book, locale)}
            </Button>
            {site.phone ? (
              <Button external={`tel:${site.phone.replace(/\s/g, "")}`} variant="outline" size="lg">
                <Icon name="phone" className="h-4 w-4" />
                {site.phone}
              </Button>
            ) : null}
          </div>

          <ul className="mt-10 flex flex-wrap gap-x-6 gap-y-3 border-t border-line pt-8">
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
        </nav>
      </div>
    </header>
  );
}
