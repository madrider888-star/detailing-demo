"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { locales, localeLabel, localeName, localePath, stripLocale, type Locale } from "@/lib/i18n";
import { ui } from "@/content/ui";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * UK / EN switch. Keeps the visitor on the same page by stripping the locale
 * prefix from the current path and re-adding the other one.
 */
export function LanguageSwitcher({
  locale,
  className,
}: {
  locale: Locale;
  className?: string;
}) {
  const pathname = usePathname();
  const basePath = stripLocale(pathname);

  return (
    <div
      className={cn("flex items-center gap-1 text-[12px] font-medium tracking-[0.14em]", className)}
      role="group"
      aria-label={t(ui.nav.languageSwitcher, locale)}
    >
      {locales.map((code, index) => {
        const active = code === locale;
        return (
          <span key={code} className="flex items-center">
            {index > 0 ? (
              <span aria-hidden="true" className="mx-1 h-3 w-px bg-line-strong" />
            ) : null}
            <Link
              href={localePath(basePath, code)}
              hrefLang={code}
              lang={code}
              aria-current={active ? "true" : undefined}
              title={localeName[code]}
              className={cn(
                "px-1 py-1 uppercase transition-colors duration-300",
                active ? "text-accent" : "text-chalk-500 hover:text-chalk-100",
              )}
            >
              {localeLabel[code]}
            </Link>
          </span>
        );
      })}
    </div>
  );
}
