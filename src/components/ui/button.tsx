import Link from "next/link";
import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "outline" | "ghost";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2.5 rounded-button font-medium uppercase " +
  "tracking-[0.12em] transition-[background-color,border-color,color,transform] duration-300 " +
  "ease-[var(--ease-out-expo)] active:translate-y-px disabled:pointer-events-none disabled:opacity-50";

const variants: Record<Variant, string> = {
  primary: "bg-accent text-ink-950 hover:brightness-110",
  outline: "border border-line-strong text-chalk-100 hover:border-accent hover:text-accent",
  ghost: "text-chalk-300 hover:text-accent",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-4 text-[11px]",
  md: "h-12 px-6 text-[12px]",
  lg: "h-14 px-8 text-[13px]",
};

interface CommonProps {
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
}

type AnchorProps = CommonProps & { href: string } & Omit<
    ComponentPropsWithoutRef<typeof Link>,
    "href" | "className" | "children"
  >;

type ExternalProps = CommonProps & { external: string } & Omit<
    ComponentPropsWithoutRef<"a">,
    "href" | "className" | "children"
  >;

type NativeProps = CommonProps & { href?: undefined; external?: undefined } & Omit<
    ComponentPropsWithoutRef<"button">,
    "className" | "children"
  >;

export type ButtonProps = AnchorProps | ExternalProps | NativeProps;

export function Button(props: ButtonProps) {
  const { variant = "primary", size = "md", className, children } = props;
  const classes = cn(base, variants[variant], sizes[size], className);

  if ("external" in props && props.external !== undefined) {
    const { external, variant: _v, size: _s, className: _c, children: _ch, ...rest } = props;
    return (
      <a href={external} className={classes} {...rest}>
        {children}
      </a>
    );
  }

  if ("href" in props && props.href !== undefined) {
    const { href, variant: _v, size: _s, className: _c, children: _ch, ...rest } = props;
    return (
      <Link href={href} className={classes} {...rest}>
        {children}
      </Link>
    );
  }

  const { variant: _v, size: _s, className: _c, children: _ch, ...rest } = props as NativeProps;
  return (
    <button className={classes} {...rest}>
      {children}
    </button>
  );
}

export function ArrowIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className={cn("h-3.5 w-3.5", className)}>
      <path
        d="M2.5 8h10M9 4.5 12.5 8 9 11.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
