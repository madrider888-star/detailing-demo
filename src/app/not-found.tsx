import { ArrowIcon, Button } from "@/components/ui/button";
import { mainNav } from "@/content/site";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Page not found",
  description: "The page you were looking for is not part of this studio.",
  robots: { index: false, follow: true },
};

export default function NotFound() {
  return (
    <section className="shell flex min-h-[70svh] flex-col justify-center py-32">
      <p className="eyebrow">
        <span aria-hidden="true" className="h-px w-8 bg-brass-600/70" />
        Error 404
      </p>
      <h1 className="mt-6 max-w-2xl text-4xl leading-[1.05] font-semibold sm:text-5xl lg:text-6xl">
        This page left the studio.
      </h1>
      <p className="mt-6 max-w-lg text-[17px] leading-relaxed text-mist-400">
        The address you followed does not match anything here. The services, pricing and gallery
        are all one click away.
      </p>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Button href="/" size="lg">
          Back to home
          <ArrowIcon />
        </Button>
        <Button href="/services" variant="secondary" size="lg">
          View services
        </Button>
      </div>

      <ul className="mt-16 flex flex-wrap gap-x-8 gap-y-3 border-t border-white/8 pt-8">
        {mainNav.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="text-[14.5px] text-mist-400 transition-colors hover:text-mist-100"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
