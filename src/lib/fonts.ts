import { Inter, Manrope } from "next/font/google";

/**
 * Both faces carry full Cyrillic coverage, which the Ukrainian copy requires.
 *
 * TODO(client): if THE BOX has its own typeface, swap the imports here — the
 * CSS variables below are what globals.css consumes, so nothing else changes.
 */
export const displayFont = Manrope({
  subsets: ["latin", "cyrillic"],
  variable: "--font-display-face",
  weight: ["500", "600", "700", "800"],
  display: "swap",
});

export const bodyFont = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-body-face",
  display: "swap",
});

export const fontClassName = `${displayFont.variable} ${bodyFont.variable}`;
