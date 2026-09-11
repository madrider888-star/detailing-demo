/**
 * Bilingual routing for THE BOX Detailing.
 *
 * Ukrainian is the default locale and lives at the site root (`/`, `/services`).
 * English is prefixed (`/en`, `/en/services`). Both language versions of every
 * string are stored in `src/content` — nothing is translated at runtime.
 */

export const locales = ["uk", "en"] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "uk";

/** A value that exists in both languages. */
export type Localized<T> = Record<Locale, T>;

/** Shorthand for the most common case: a translated string. */
export type LocalizedText = Localized<string>;

/** `lang` attribute and hreflang code for each locale. */
export const localeTag: Record<Locale, string> = {
  uk: "uk-UA",
  en: "en",
};

/** Label shown in the language switcher. */
export const localeLabel: Record<Locale, string> = {
  uk: "UK",
  en: "EN",
};

export const localeName: Record<Locale, string> = {
  uk: "Українська",
  en: "English",
};

/** Prefixes an internal path with the locale segment. */
export function localePath(path: string, locale: Locale): string {
  const clean = path === "/" ? "" : path;
  if (locale === defaultLocale) return clean === "" ? "/" : clean;
  return `/en${clean}`;
}

/** Removes the locale prefix, returning the shared route (always starts with `/`). */
export function stripLocale(pathname: string): string {
  if (pathname === "/en") return "/";
  if (pathname.startsWith("/en/")) return pathname.slice(3);
  return pathname;
}

/** Reads the locale out of a pathname. */
export function localeFromPath(pathname: string): Locale {
  return pathname === "/en" || pathname.startsWith("/en/") ? "en" : "uk";
}

/** Picks one language out of a localized value. */
export function t<T>(value: Localized<T>, locale: Locale): T {
  return value[locale];
}

/** Picks one language, tolerating content that has not been filled in yet. */
export function maybeT<T>(
  value: Localized<T> | null | undefined,
  locale: Locale,
): T | null {
  return value ? value[locale] : null;
}

/**
 * "12 робіт" / "12 projects" — picks the right plural form for a count.
 * `forms` is [one, few, many] for Ukrainian and [one, many] for English.
 */
export function countLabel(
  n: number,
  forms: Localized<readonly string[]>,
  locale: Locale,
): string {
  const words = forms[locale];
  if (locale === "uk") {
    const mod10 = n % 10;
    const mod100 = n % 100;
    const form =
      mod10 === 1 && mod100 !== 11
        ? words[0]
        : mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)
          ? words[1]
          : words[2];
    return `${n} ${form}`;
  }
  return `${n} ${n === 1 ? words[0] : words[words.length - 1]}`;
}
