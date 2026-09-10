import { SiteShell } from "@/views/site-shell";
import { NotFoundView } from "@/views/not-found-view";
import { defaultLocale } from "@/lib/i18n";
import "@/app/globals.css";

export const metadata = { title: "404", robots: { index: false, follow: true } };

/**
 * Catches URLs that match no route at all. Ukrainian is used because it is the
 * default locale; `/en/...` misses are handled by (en)/en/not-found.tsx, which
 * does inherit the English shell.
 */
export default function NotFound() {
  return (
    <SiteShell locale={defaultLocale}>
      <NotFoundView locale={defaultLocale} />
    </SiteShell>
  );
}
