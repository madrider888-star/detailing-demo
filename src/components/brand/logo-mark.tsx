import type { ComponentPropsWithoutRef } from "react";
import { LOGO_LETTERS, LOGO_VIEWBOX } from "@/components/brand/logo-paths";
import { cn } from "@/lib/utils";

/**
 * The studio's wordmark as inline SVG. Takes its colour from `currentColor`,
 * so `text-chalk-50` (or the accent) styles it like text. Each letter is its
 * own <path data-letter> so the intro animation can address them one by one.
 */
export function LogoMark({
  title,
  className,
  ...rest
}: { title?: string } & Omit<ComponentPropsWithoutRef<"svg">, "viewBox" | "children">) {
  return (
    <svg
      viewBox={LOGO_VIEWBOX}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : "true"}
      className={cn("block h-auto fill-current", className)}
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      {LOGO_LETTERS.map((letter) => (
        <path key={letter.id} d={letter.d} data-letter={letter.id} />
      ))}
    </svg>
  );
}
