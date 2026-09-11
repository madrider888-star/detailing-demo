import Image from "next/image";
import { ArrowIcon, Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Magnetic } from "@/components/ui/magnetic";
import { site } from "@/content/site";
import { ui } from "@/content/ui";
import { localePath, t, type Locale } from "@/lib/i18n";
import type { Photo } from "@/types";

export function CTASection({
  locale,
  eyebrow,
  title,
  description,
  media,
}: {
  locale: Locale;
  eyebrow?: string;
  title?: string;
  description?: string;
  media?: Photo | null;
}) {
  const phone = site.phone;

  return (
    <section className="relative isolate overflow-hidden border-y border-line">
      {media ? (
        <div aria-hidden="true" className="absolute inset-0 -z-10">
          <Image src={media.src} alt="" fill sizes="100vw" className="object-cover opacity-45" />
          <div className="absolute inset-0 bg-gradient-to-r from-ink-950 via-ink-950/85 to-ink-950/50" />
        </div>
      ) : null}

      <div className="shell py-20 sm:py-24 lg:py-32">
        <div className="max-w-3xl">
          <p className="eyebrow">
            <span aria-hidden="true" className="h-px w-8 bg-accent-muted" />
            {eyebrow ?? t(ui.sections.contactEyebrow, locale)}
          </p>
          <h2 className="display-xl mt-6 text-[2.25rem] sm:text-[3rem] lg:text-[3.75rem]">
            {title ?? t(ui.sections.contactTitle, locale)}
          </h2>
          {description ? (
            <p className="mt-6 text-[16.5px] leading-relaxed text-chalk-300">{description}</p>
          ) : null}

          <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Magnetic>
              <Button href={localePath("/contact", locale)} size="lg" className="w-full sm:w-auto">
                {t(ui.actions.book, locale)}
                <ArrowIcon />
              </Button>
            </Magnetic>
            {phone ? (
              <Button external={`tel:${phone.replace(/\s/g, "")}`} variant="outline" size="lg">
                <Icon name="phone" className="h-4 w-4" />
                {phone}
              </Button>
            ) : (
              <Button external={site.instagram.url} variant="outline" size="lg">
                <Icon name="instagram" className="h-4 w-4" />
                {site.instagram.handle}
              </Button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
