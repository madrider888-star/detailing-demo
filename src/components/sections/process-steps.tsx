import { Reveal } from "@/components/ui/reveal";
import type { ProcessStep } from "@/types";
import { cn } from "@/lib/utils";

interface ProcessStepsProps {
  steps: ProcessStep[];
  /** `rail` draws the connecting line used on long-form pages. */
  variant?: "rail" | "grid";
  className?: string;
}

export function ProcessSteps({ steps, variant = "rail", className }: ProcessStepsProps) {
  if (variant === "grid") {
    return (
      <ol className={cn("grid gap-px overflow-hidden sm:grid-cols-2 lg:grid-cols-3", className)}>
        {steps.map((step, index) => (
          <Reveal
            as="li"
            key={step.title}
            delay={index * 70}
            className="relative bg-carbon-850 p-7 outline outline-white/8 sm:p-8"
          >
            <span className="font-display text-[13px] font-medium tracking-[0.2em] text-brass-500">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h3 className="mt-5 font-display text-lg font-medium">{step.title}</h3>
            <p className="mt-3 text-[14.5px] leading-relaxed text-mist-400">{step.description}</p>
            {step.duration ? (
              <p className="mt-5 text-[12px] tracking-[0.16em] text-mist-500 uppercase">
                {step.duration}
              </p>
            ) : null}
          </Reveal>
        ))}
      </ol>
    );
  }

  return (
    <ol className={cn("relative", className)}>
      <span
        aria-hidden="true"
        className="absolute top-2 bottom-2 left-[15px] w-px bg-gradient-to-b from-brass-600/50 via-white/10 to-transparent"
      />
      {steps.map((step, index) => (
        <Reveal
          as="li"
          key={step.title}
          delay={index * 60}
          className="relative grid grid-cols-[32px_1fr] gap-x-6 pb-10 last:pb-0 sm:grid-cols-[32px_1fr]"
        >
          <span className="relative z-10 mt-0.5 grid h-8 w-8 place-items-center rounded-full border border-white/12 bg-carbon-900 font-display text-[12px] font-medium text-brass-400">
            {String(index + 1).padStart(2, "0")}
          </span>
          <div className="pt-1">
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <h3 className="font-display text-lg font-medium">{step.title}</h3>
              {step.duration ? (
                <span className="text-[12px] tracking-[0.16em] text-mist-500 uppercase">
                  {step.duration}
                </span>
              ) : null}
            </div>
            <p className="mt-2.5 max-w-2xl text-[15px] leading-relaxed text-mist-400">
              {step.description}
            </p>
          </div>
        </Reveal>
      ))}
    </ol>
  );
}
