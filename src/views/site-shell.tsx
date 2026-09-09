import type { ReactNode } from "react";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { ui } from "@/content/ui";
import { fontClassName } from "@/lib/fonts";
import { localeTag, t, type Locale } from "@/lib/i18n";
import { localBusinessJsonLd } from "@/lib/seo";

/**
 * The document shell. Ukrainian and English each have their own root layout so
 * `<html lang>` is correct per language; both render this shared shell.
 */
export function SiteShell({ locale, children }: { locale: Locale; children: ReactNode }) {
  return (
    <html lang={localeTag[locale]} className={fontClassName}>
      <body className="min-h-screen antialiased">
        <noscript>
          {/* Scroll-reveal elements start hidden; without JS they must not stay that way. */}
          <style>{"[data-reveal]{opacity:1!important;transform:none!important}"}</style>
        </noscript>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-100 focus:bg-accent focus:px-5 focus:py-3 focus:text-sm focus:font-medium focus:text-ink-950"
        >
          {t(ui.nav.skipToContent, locale)}
        </a>
        <Header locale={locale} />
        <main id="main">{children}</main>
        <Footer locale={locale} />
        <script
          type="application/ld+json"
          // Built from the studio's own confirmed details in content/site.ts.
          dangerouslySetInnerHTML={{ __html: JSON.stringify(localBusinessJsonLd(locale)) }}
        />
      </body>
    </html>
  );
}
