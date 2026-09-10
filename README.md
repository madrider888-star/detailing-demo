# THE BOX Detailing

Bilingual (Ukrainian / English) website for THE BOX Detailing — Instagram
[@thebox.detailing](https://www.instagram.com/thebox.detailing/).

**Stack:** Next.js 16 (App Router) · React 19 · TypeScript (strict) · Tailwind CSS v4.
The only runtime dependencies are `next`, `react` and `react-dom`.

> **Status: awaiting content.** The site's structure, design system and both
> language trees are complete. The studio's real photographs, logo, contact
> details and service list have not been supplied yet, so the content files are
> empty skeletons. Sections with no content hide themselves, so the site builds
> and runs — it simply has little to show until the material arrives. Nothing on
> the site is invented.

## Running it locally

```bash
npm install
npm run dev        # http://localhost:3000
```

| Script              | What it does                        |
| ------------------- | ----------------------------------- |
| `npm run dev`       | Development server with fast refresh |
| `npm run build`     | Production build                     |
| `npm start`         | Serve the production build           |
| `npm run lint`      | ESLint                               |
| `npm run typecheck` | `tsc --noEmit`                       |

## Languages

Ukrainian is the default and lives at the root. English is prefixed with `/en`.

| Page      | Ukrainian            | English                 |
| --------- | -------------------- | ----------------------- |
| Home      | `/`                  | `/en`                   |
| Services  | `/services`          | `/en/services`          |
| Service   | `/services/[slug]`   | `/en/services/[slug]`   |
| Portfolio | `/portfolio`         | `/en/portfolio`         |
| Project   | `/portfolio/[slug]`  | `/en/portfolio/[slug]`  |
| Studio    | `/about`             | `/en/about`             |
| Contact   | `/contact`           | `/en/contact`           |

Nothing is machine-translated. Every string exists in both languages in the
content files, written as a pair:

```ts
title: { uk: "Керамічне покриття", en: "Ceramic Coating" }
```

Change the `uk` value to edit the Ukrainian, the `en` value for English. The
UK / EN switch in the header keeps the visitor on the same page.

## Files you can edit yourself

Everything a non-developer needs to change lives in **`src/content/`**. You never
need to touch a component.

| File                       | What it holds                                                        |
| -------------------------- | -------------------------------------------------------------------- |
| **`site.ts`**              | Phone, e-mail, address, opening hours, Instagram, messengers, hero copy |
| **`services.ts`**          | The service list                                                     |
| **`projects.ts`**          | Portfolio projects                                                   |
| **`reviews.ts`**           | Client reviews                                                       |
| **`faq.ts`**               | Frequently asked questions                                           |
| **`about.ts`**             | Studio story, philosophy, process, equipment, materials              |
| **`ui.ts`**                | Button and label wording (both languages)                            |

Each file opens with instructions and a filled-in template you can copy.

### Where the phone number and contacts live

**`src/content/site.ts`, and nowhere else.** Change it once and it updates in the
header, the footer, the contact page, every call button, the booking form and
the Google structured data.

```ts
phone: "+380 XX XXX XX XX",
email: "hello@example.com",
address: { street: { uk: "...", en: "..." }, city: { uk: "...", en: "..." }, ... },
hours: [{ days: { uk: "Пн – Пт", en: "Mon – Fri" }, time: { uk: "10:00 – 20:00", en: "10:00 – 20:00" } }],
instagram: { handle: "@thebox.detailing", url: "https://www.instagram.com/thebox.detailing/" },
messaging: [{ label: "Telegram", href: "https://t.me/...", icon: "telegram" }],
```

Fields left as `null` are hidden on the site rather than shown empty, so it is
safe to fill them in one at a time.

### How to add a portfolio project

1. Create `public/images/portfolio/<slug>/` and put the photos in it.
2. Open `src/content/projects.ts` and copy the template at the bottom of the file
   into the `projects` array.
3. Fill in `slug`, `vehicle`, `title`, `description`, and the photo paths.
4. `serviceSlugs` must match slugs from `services.ts` — that is what links the
   project to the services it used, in both directions.
5. `beforeAfter` pairs power the drag-to-compare slider; leave the array empty if
   you have no matched pairs.
6. Set `featured: true` to show it on the home page.

The project page, the portfolio filter and the sitemap update themselves.

### How to add a service

1. Create `public/images/services/<slug>/` and put the photos in it.
2. Open `src/content/services.ts` and copy the template at the bottom of the file
   into the `services` array.
3. Give it a unique `slug` — it becomes `/services/<slug>` and `/en/services/<slug>`.
4. Leave `price: null` to display "Ціна за запитом" / "Contact for price", or set
   it to a real figure: `price: { uk: "від 12 000 ₴", en: "from ₴12,000" }`.
5. Set `featured: true` to show it on the home page.

It appears automatically on the services page, in the booking form dropdown and
in the sitemap.

## Design system

All visual decisions live in **`src/app/globals.css`**. Colours, typography,
corner radius and spacing are declared once as tokens and used everywhere
through Tailwind utilities.

- **`--color-accent`** is currently white, which renders the site as a deliberate
  monochrome. Set it to THE BOX's brand colour and every eyebrow, active state,
  focus ring and highlight picks it up.
- **`--radius-card` / `--radius-button`** control the geometry of the whole UI.
- Fonts are loaded in `src/lib/fonts.ts` (Manrope + Inter, both with full
  Cyrillic coverage). Swap the imports there to change typography.
- The logo is `src/components/layout/logo.tsx` — set `LOGO_SRC` to the logo file
  and it replaces the typographic wordmark.

## Booking form

There is no server. The form validates, composes the enquiry as text and hands it
to whichever channel the studio uses (WhatsApp link, or e-mail), with a
copy-to-clipboard fallback. Configure the target with `bookingChannel` in
`site.ts`. To send through a backend later, replace the `handoff()` function in
`src/components/forms/booking-form.tsx` — nothing else changes.

## SEO

Per-page metadata and canonical URLs, `hreflang` pairing between the Ukrainian
and English versions of every page, Open Graph and Twitter cards, a generated PNG
social image, a sitemap covering both languages, `robots.txt`, and `LocalBusiness`
structured data built only from confirmed details.

There is deliberately **no `aggregateRating`** in the structured data. Publishing
invented review scores breaches Google's guidelines and risks a manual penalty;
it will be added if and when real reviews exist.

## Project structure

```
public/images/          Photographs (portfolio/, services/, hero/, brand/)
src/
  app/
    (uk)/               Ukrainian routes at /
    (en)/en/            English routes at /en
    sitemap.ts robots.ts icon.svg opengraph-image.tsx
  views/                One implementation per page, rendered by both languages
  components/
    layout/             Header, Footer, Logo, LanguageSwitcher
    sections/           Hero, PageHeader, PortfolioGrid, PhotoGallery,
                        BeforeAfter, ProcessSteps, FAQ, Reviews, CTA, Instagram
    cards/              ServiceCard, ProjectCard, ReviewCard
    forms/              BookingForm
    ui/                 Button, Section, SectionTitle, Badge, SpecList,
                        Accordion, Icon, Reveal
  content/              ← everything you edit
  lib/                  i18n helpers, metadata helpers, fonts, cn()
  types/                Content model
```

Each page exists once in `src/views/` and is rendered by two thin route files,
one per language, so the two versions can never drift apart.
