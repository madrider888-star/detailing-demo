import Link from "next/link";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  /** Hides the wordmark and renders the apex mark alone. */
  markOnly?: boolean;
}

export function Logo({ className, markOnly = false }: LogoProps) {
  return (
    <Link
      href="/"
      aria-label="Apex Detailing — home"
      className={cn("group inline-flex items-center gap-3", className)}
    >
      <svg
        viewBox="0 0 32 32"
        fill="none"
        aria-hidden="true"
        className="h-8 w-8 shrink-0 text-mist-100 transition-colors duration-300 group-hover:text-brass-400"
      >
        <path
          d="M16 3.5 29 28.5H22.6L16 15.2 9.4 28.5H3L16 3.5Z"
          fill="currentColor"
          fillOpacity="0.92"
        />
        <path d="M16 18.6 20.6 28.5h-9.2L16 18.6Z" fill="currentColor" fillOpacity="0.45" />
      </svg>
      {markOnly ? null : (
        <span className="flex flex-col leading-none">
          <span className="font-display text-[15px] font-semibold tracking-[0.2em] text-mist-100 uppercase">
            Apex
          </span>
          <span className="mt-1 text-[9px] font-medium tracking-[0.34em] text-mist-500 uppercase">
            Detailing
          </span>
        </span>
      )}
    </Link>
  );
}
