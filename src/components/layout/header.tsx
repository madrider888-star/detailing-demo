"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/layout/logo";
import { Button } from "@/components/ui/button";
import { mainNav, site } from "@/content/site";
import { cn } from "@/lib/utils";

export function Header() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [lastPath, setLastPath] = useState(pathname);

  // Close the drawer whenever the route changes, without an extra effect pass.
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

  // Lock background scrolling while the drawer is open.
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

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-500",
        scrolled || menuOpen
          ? "glass border-b border-white/8"
          : "border-b border-transparent bg-transparent",
      )}
    >
      <div className="shell flex h-18 items-center justify-between gap-6 sm:h-20">
        <Logo />

        <nav aria-label="Primary" className="hidden lg:block">
          <ul className="flex items-center gap-1">
            {mainNav.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={isActive(item.href) ? "page" : undefined}
                  className={cn(
                    "relative rounded-full px-4 py-2 text-[13.5px] font-medium transition-colors duration-300",
                    isActive(item.href)
                      ? "text-mist-100"
                      : "text-mist-400 hover:text-mist-100",
                  )}
                >
                  {item.label}
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute inset-x-4 -bottom-0.5 h-px bg-brass-500 transition-transform duration-300",
                      isActive(item.href) ? "scale-x-100" : "scale-x-0",
                    )}
                  />
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="hidden items-center gap-5 lg:flex">
          <a
            href={`tel:${site.phoneHref}`}
            className="text-[13.5px] font-medium text-mist-300 transition-colors hover:text-mist-100"
          >
            {site.phone}
          </a>
          <Button href="/contact" size="sm">
            Book Detailing
          </Button>
        </div>

        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-controls="mobile-navigation"
          className="-mr-2 grid h-11 w-11 place-items-center rounded-full text-mist-200 transition-colors hover:text-mist-100 lg:hidden"
        >
          <span className="sr-only">{menuOpen ? "Close menu" : "Open menu"}</span>
          <span aria-hidden="true" className="relative block h-4 w-6">
            <span
              className={cn(
                "absolute left-0 block h-px w-6 bg-current transition-transform duration-300",
                menuOpen ? "top-2 rotate-45" : "top-1",
              )}
            />
            <span
              className={cn(
                "absolute left-0 block h-px w-6 bg-current transition-transform duration-300",
                menuOpen ? "top-2 -rotate-45" : "top-3",
              )}
            />
          </span>
        </button>
      </div>

      {/* Solid panel rather than glass: a backdrop filter nested inside the
          header's own filter does not composite, leaving the page readable
          through the drawer. */}
      <div
        id="mobile-navigation"
        hidden={!menuOpen}
        className="fixed inset-x-0 top-18 bottom-0 overflow-y-auto overscroll-contain border-t border-white/8 bg-carbon-950 sm:top-20 lg:hidden"
      >
        <nav aria-label="Mobile" className="shell py-8">
          <ul className="flex flex-col">
            {mainNav.map((item) => (
              <li key={item.href} className="border-b border-white/6 last:border-0">
                <Link
                  href={item.href}
                  aria-current={isActive(item.href) ? "page" : undefined}
                  className={cn(
                    "flex items-center justify-between py-4 font-display text-xl font-medium transition-colors",
                    isActive(item.href) ? "text-brass-400" : "text-mist-100",
                  )}
                >
                  {item.label}
                  <span aria-hidden="true" className="text-mist-500">
                    &rarr;
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <div className="mt-9 flex flex-col gap-3">
            <Button href="/contact" size="lg">
              Book Detailing
            </Button>
            <a
              href={`tel:${site.phoneHref}`}
              className="flex h-13 items-center justify-center rounded-full border border-white/12 text-[15px] font-medium text-mist-200"
            >
              {site.phone}
            </a>
          </div>

          <address className="mt-10 space-y-2 border-t border-white/8 pt-8 text-[14px] not-italic text-mist-400">
            <p>{site.address.street}</p>
            <p>
              {site.address.city}, {site.address.postalCode}
            </p>
            <a
              href={`mailto:${site.email}`}
              className="inline-block pt-2 text-mist-300 transition-colors hover:text-mist-100"
            >
              {site.email}
            </a>
          </address>
        </nav>
      </div>
    </header>
  );
}
