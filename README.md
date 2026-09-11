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
| **`projects.ts`**          | Projects added by hand (Instagram ones come from `work/selection.json`) |
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

## "Our work" — importing projects from Instagram

The portfolio is built from the studio's own Instagram posts. Photos and videos
are copied into the repository, so nothing on the site depends on Instagram's
servers.

```bash
npm run import:instagram -- ~/Downloads/instagram-export.json
```

The export (an Apify Instagram-scraper dataset) is read from wherever you keep
it. **Never copy it into the repository** — its media links are signed, expire,
and must not reach the client bundle. Running the import again is safe: it
rebuilds the project list from scratch and skips files already on disk, so
nothing is duplicated.

| Input / output                           | Purpose                                                        |
| ---------------------------------------- | -------------------------------------------------------------- |
| `src/content/work/selection.json`        | Which posts become projects: exclusions (with reasons), reel + carousel merges, the 12 featured projects, which reels are downloaded, vehicle name spelling, filter categories, summaries |
| `src/content/work/glossary.json`         | Every service phrase from the captions in Ukrainian and English |
| `src/content/work/projects.generated.json` | What the site renders — rewritten by every import, do not edit |
| `src/content/work/import-report.json`    | Untranslated phrases and media that failed to download          |
| `src/content/work/services.generated.json` | The service catalogue for /services — rewritten by `npm run work:services`, do not edit |
| `public/work/<slug>/`                    | Photos (resized to 1600 px), reel posters and downloaded reels  |

A project appears on the site only when it has a cover photo on disk — so until
the media has been downloaded the section simply shows nothing. Videos are
downloaded only for projects listed under `"videos"` in `selection.json`; every
other reel shows its poster with a link to the post on Instagram. On the page a
video loads only when the visitor presses play.

To hide a project add its shortCode to `"hidden"`; to change its car name edit
`"vehicleAliases"`; to fix a translation edit `glossary.json` — then run the
import again. Projects that were never on Instagram go in `src/content/projects.ts`.

Options: `--skip-media` (rebuild the list only), `--videos=all|selected|none`,
`--max-video-mb=40`.

### The service catalogue — what the studio does

`/services` and the home page list every service the studio offers. That list is
not written by hand: it is distilled from the work lines of the imported
projects, so it contains only work the studio has actually published, and each
service shows how many projects it appears in.

```bash
npm run work:services
```

`scripts/build-service-catalog.mjs` reads `projects.generated.json`, folds the
many wordings of the same job ("Бронювання внутрішніх прорізів дверей",
"Обклеювання внутрішніх прорізів дверей", "Дверні прорізи" …) into one canonical
service each, groups them by the portfolio categories from `selection.json` and
writes `src/content/work/services.generated.json`. Run it after every Instagram
import. Lines no rule recognises are printed at the end and stored under
`"unmatched"` in the output — add a rule in the script for them. The
`"sources"` list next to each service shows every original wording it covers,
which is the place to check that nothing was merged wrongly.

Detailed service pages with prices and photos still come from `services.ts`
(see "How to add a service"); the catalogue is the complete, de-duplicated list.

Every imported post is remembered in `src/content/work/posts.archive.json`
(captions and dates only — no media links), so an export that contains just the
latest posts is merged over what is already there and older projects never
disappear. The importer also stores a tiny blurred preview of every photo in the
manifest; the site shows it while the real photo loads.

### Automatic weekly sync

`.github/workflows/sync-instagram.yml` fetches the studio's newest posts from
Apify every Monday (or on demand from the **Actions** tab), runs the importer
and commits the result to `main`, which Vercel deploys. To switch it on add one
repository secret: **Settings → Secrets and variables → Actions → New
repository secret** named `APIFY_TOKEN` (from
<https://console.apify.com/account#/integrations>). Optional variables:
`APIFY_ACTOR` (default `apify~instagram-scraper`) and `SYNC_POSTS` (default 30).

Downloading media from a machine behind a restricted network needs these hosts
allowed: `*.cdninstagram.com`, `www.instagram.com`, `*.fbcdn.net` and
`*.fna.fbcdn.net`.

## Motion

- **Hero clip** — `site.hero.video` in `site.ts` names a short reel from
  `public/work`; the poster paints first, the clip fades in once it plays and is
  never loaded for visitors who prefer reduced motion or data saving.
- **Route transitions** — pages fade/ease between each other and a project's
  cover morphs from its tile into the project page (React `<ViewTransition>`,
  CSS in `globals.css`). Browsers without the API simply cut.
- **Blur-up photos**, a **scroll parallax** on large photographs (pure CSS),
  **magnetic** primary buttons and a **pointer ring** on mouse devices. All of
  it respects `prefers-reduced-motion`.
- **Lightbox** — swipe, arrow keys, counter, thumbnail strip and tap-to-zoom.

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

## Booking form → Telegram

The form posts to `/api/lead`, which forwards each request as one message to
the studio's Telegram. Two environment variables switch it on (Vercel →
Project → Settings → Environment Variables, then redeploy):

| Variable             | Value                                                                 |
| -------------------- | --------------------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Token of a bot created with [@BotFather](https://t.me/BotFather)      |
| `TELEGRAM_CHAT_ID`   | Id of the chat that should receive requests (the owner's chat or a group the bot was added to) |

To find the chat id: open the bot, press **Start**, then visit
`https://api.telegram.org/bot<TOKEN>/getUpdates` — the number under
`message.chat.id` is it. Requests are rate-limited per IP, a honeypot field
drops bots, and nothing is stored on the server.

Until the variables are set the endpoint answers "not configured" and the form
falls back to its original behaviour: it composes the enquiry as text and opens
the studio's messenger or e-mail with it prefilled (`bookingChannel` in
`site.ts`), with a copy-to-clipboard button.

On phones a bar with **Call / Message / Book** stays pinned to the bottom of
every page except the contact page.

## SEO

Per-page metadata and canonical URLs, `hreflang` pairing between the Ukrainian
and English versions of every page, Open Graph and Twitter cards, a sitemap
covering both languages, `robots.txt`, and `LocalBusiness` structured data built
only from confirmed details.

Social cards are photographic: every project page gets its own 1200×630 image
built from the cover photo, the car's name and the first lines of work
(`src/lib/og.tsx`), so links shared in messengers preview like a magazine
cover. The home page card uses the hero clip's poster.

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
