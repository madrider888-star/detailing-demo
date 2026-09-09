import Image from "next/image";
import Link from "next/link";
import { localePath, type Locale } from "@/lib/i18n";
import { site } from "@/content/site";
import { cn } from "@/lib/utils";

/**
 * TODO(client): drop the studio's logo into public/images/brand/ and set the
 * path here (SVG preferred). While this is null the wordmark below is used.
 *
 *   const LOGO_SRC = "/images/brand/logo.svg";
 */
const LOGO_SRC: string | null = null;
const LOGO_ASPECT = 4.2; // width ÷ height of the logo file

export function Logo({ locale, className }: { locale: Locale; className?: string }) {
  return (
    <Link
      href={localePath("/", locale)}
      aria-label={site.name}
      className={cn("group inline-flex items-center", className)}
    >
      {LOGO_SRC ? (
        <span
          className="relative block h-7 sm:h-8"
          style={{ aspectRatio: String(LOGO_ASPECT) }}
        >
          <Image src={LOGO_SRC} alt={site.name} fill priority className="object-contain" />
        </span>
      ) : (
        <span className="flex items-baseline gap-2 leading-none">
          <span className="font-display text-[17px] font-bold tracking-[0.24em] text-chalk-50 uppercase transition-colors duration-300 group-hover:text-accent sm:text-lg">
            The&nbsp;Box
          </span>
          <span className="hidden text-[9px] font-medium tracking-[0.36em] text-chalk-500 uppercase sm:inline">
            Detailing
          </span>
        </span>
      )}
    </Link>
  );
}
