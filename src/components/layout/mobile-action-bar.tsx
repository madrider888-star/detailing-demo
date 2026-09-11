"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Icon, type IconName } from "@/components/ui/icon";
import { site } from "@/content/site";
import { ui } from "@/content/ui";
import { localePath, stripLocale, t, type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * Thumb-reach actions pinned to the bottom of phone screens: call, message,
 * book. It slides in once the visitor scrolls past the hero and stays out of
 * the way on the contact page, where the form itself is the action.
 */
export function MobileActionBar({ locale }: { locale: Locale }) {
  const pathname = usePathname();
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const onScroll = () => setShown(window.scrollY > 320);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (stripLocale(pathname) === "/contact") return null;

  const phone = site.phone ? `tel:${site.phone.replace(/\s/g, "")}` : null;
  const messenger =
    site.messaging.find((channel) => channel.icon === "telegram") ??
    site.messaging.find((channel) => channel.icon === "whatsapp") ??
    site.messaging[0] ??
    null;
  const write: { href: string; icon: IconName; label: string } = messenger
    ? { href: messenger.href, icon: messenger.icon, label: messenger.label }
    : { href: site.instagram.dm, icon: "instagram", label: "Instagram" };

  return (
    <div
      className={cn(
        "fixed inset-x-0 bottom-0 z-40 border-t border-line bg-ink-950/95 backdrop-blur-md transition-transform duration-500 ease-[var(--ease-out-expo)] lg:hidden",
        "pb-[env(safe-area-inset-bottom)]",
        shown ? "translate-y-0" : "translate-y-full",
      )}
      aria-hidden={!shown}
    >
      <div className="grid grid-cols-3 divide-x divide-line">
        {phone ? (
          <a href={phone} className="flex h-14 flex-col items-center justify-center gap-1 text-chalk-100">
            <Icon name="phone" className="h-4 w-4" />
            <span className="text-[10px] font-medium tracking-[0.16em] uppercase">
              {t(ui.actions.call, locale)}
            </span>
          </a>
        ) : (
          <span />
        )}
        <a
          href={write.href}
          target="_blank"
          rel="noreferrer noopener"
          className="flex h-14 flex-col items-center justify-center gap-1 text-chalk-100"
        >
          <Icon name={write.icon} className="h-4 w-4" />
          <span className="text-[10px] font-medium tracking-[0.16em] uppercase">{write.label}</span>
        </a>
        <Link
          href={localePath("/contact", locale)}
          className="flex h-14 flex-col items-center justify-center gap-1 bg-accent text-ink-950"
        >
          <span className="text-[11px] font-semibold tracking-[0.16em] uppercase">
            {t(ui.actions.book, locale)}
          </span>
        </Link>
      </div>
    </div>
  );
}
