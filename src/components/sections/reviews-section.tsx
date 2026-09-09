import { ReviewCard } from "@/components/cards/review-card";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { reviews } from "@/content/reviews";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";

export function ReviewsSection({ locale }: { locale: Locale }) {
  if (reviews.length === 0) return null;

  return (
    <Section aria-labelledby="reviews-title">
      <SectionTitle
        id="reviews-title"
        eyebrow={t(ui.sections.reviewsEyebrow, locale)}
        title={t(ui.sections.reviewsTitle, locale)}
      />
      <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {reviews.map((review, index) => (
          <Reveal as="li" key={review.author} delay={index * 60} className="h-full">
            <ReviewCard review={review} locale={locale} />
          </Reveal>
        ))}
      </ul>
    </Section>
  );
}
