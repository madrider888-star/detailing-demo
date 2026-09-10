import { t, type Locale } from "@/lib/i18n";
import type { Review } from "@/types";
import { cn } from "@/lib/utils";

function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex gap-1" role="img" aria-label={`${rating}/5`}>
      {Array.from({ length: 5 }, (_, index) => (
        <svg
          key={index}
          viewBox="0 0 16 16"
          aria-hidden="true"
          className={cn("h-3.5 w-3.5", index < rating ? "text-accent" : "text-ink-600")}
        >
          <path
            fill="currentColor"
            d="M8 1.6l1.85 3.9 4.15.6-3 3.02.71 4.28L8 11.36 4.29 13.4 5 9.12 2 6.1l4.15-.6L8 1.6Z"
          />
        </svg>
      ))}
    </div>
  );
}

export function ReviewCard({
  review,
  locale,
  className,
}: {
  review: Review;
  locale: Locale;
  className?: string;
}) {
  return (
    <figure
      className={cn("flex h-full flex-col rounded-card border border-line bg-ink-850 p-7", className)}
    >
      {review.rating ? <Stars rating={review.rating} /> : null}
      <blockquote className="mt-5 flex-1">
        <p className="text-[15.5px] leading-relaxed text-chalk-200">
          &ldquo;{t(review.text, locale)}&rdquo;
        </p>
      </blockquote>
      <figcaption className="rule mt-7 pt-5">
        <p className="font-display text-[15px] font-medium text-chalk-50">{review.author}</p>
        {review.vehicle ? <p className="mt-1 text-[13px] text-chalk-500">{review.vehicle}</p> : null}
        {review.source ? (
          <p className="mt-2 text-[11px] tracking-[0.16em] text-accent uppercase">{review.source}</p>
        ) : null}
      </figcaption>
    </figure>
  );
}
