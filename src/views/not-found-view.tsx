import Link from "next/link";
import { ArrowIcon, Button } from "@/components/ui/button";
import { mainNav } from "@/content/site";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";

export function NotFoundView({ locale }: { locale: Locale }) {
  return (
    <section className="shell flex min-h-[70svh] flex-col justify-center py-32">
      <p className="eyebrow">
        <span aria-hidden="true" className="h-px w-8 bg-accent-muted" />
        {t(ui.notFound.eyebrow, locale)}
      </p>
      <h1 className="display-xl mt-6 max-w-3xl text-[2.5rem] sm:text-[3.5rem] lg:text-[4.5rem]">
        {t(ui.notFound.title, locale)}
      </h1>
      <p className="mt-6 max-w-lg text-[17px] leading-relaxed text-chalk-400">
        {t(ui.notFound.body, locale)}
      </p>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Button href={localePath("/", locale)} size="lg">
          {t(ui.actions.backHome, locale)}
          <ArrowIcon />
        </Button>
        <Button href={localePath("/portfolio", locale)} variant="outline" size="lg">
          {t(ui.actions.viewPortfolio, locale)}
        </Button>
      </div>

      <ul className="mt-16 flex flex-wrap gap-x-8 gap-y-3 border-t border-line pt-8">
        {mainNav.map((item) => (
          <li key={item.href}>
            <Link
              href={localePath(item.href, locale)}
              className="text-[13px] tracking-[0.14em] text-chalk-400 uppercase transition-colors hover:text-accent"
            >
              {t(item.label, locale)}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
