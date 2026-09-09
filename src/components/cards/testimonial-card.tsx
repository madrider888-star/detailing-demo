import type { Testimonial } from "@/types";
import { cn } from "@/lib/utils";

function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex gap-1" role="img" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: 5 }, (_, index) => (
        <svg
          key={index}
          viewBox="0 0 16 16"
          aria-hidden="true"
          className={cn("h-3.5 w-3.5", index < rating ? "text-brass-500" : "text-carbon-600")}
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

export function TestimonialCard({
  testimonial,
  className,
}: {
  testimonial: Testimonial;
  className?: string;
}) {
  return (
    <figure
      className={cn(
        "flex h-full flex-col rounded-2xl border border-white/8 bg-carbon-850 p-7 sm:p-8",
        className,
      )}
    >
      <Stars rating={testimonial.rating} />
      <blockquote className="mt-5 flex-1">
        <p className="text-[15.5px] leading-relaxed text-mist-200">&ldquo;{testimonial.quote}&rdquo;</p>
      </blockquote>
      <figcaption className="rule mt-7 pt-5">
        <p className="font-display text-[15px] font-medium text-mist-100">{testimonial.author}</p>
        <p className="mt-1 text-[13px] text-mist-500">{testimonial.vehicle}</p>
        <p className="mt-2.5 text-[12px] tracking-[0.14em] text-brass-500 uppercase">
          {testimonial.service}
        </p>
      </figcaption>
    </figure>
  );
}
