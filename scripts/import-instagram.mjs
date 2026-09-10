#!/usr/bin/env node
/**
 * Imports THE BOX Detailing's Instagram work into the site's portfolio.
 *
 *   node scripts/import-instagram.mjs <path/to/instagram-export.json> [options]
 *
 *   --skip-media          Write the manifest without downloading anything.
 *   --videos=selected     Download videos only for projects listed under
 *                         "videos" in selection.json (default).
 *   --videos=all|none     Download every reel video, or none.
 *   --max-video-mb=40     Skip videos larger than this.
 *
 * INPUT  The Apify/Instagram export. It is read from wherever you keep it and
 *        is never copied into the repository: its media URLs are signed and
 *        expire, and they must not end up in the client bundle.
 * CURATION  src/content/work/selection.json  (which posts, merges, vehicles,
 *        categories, featured order)  and  src/content/work/glossary.json
 *        (every service phrase in Ukrainian and English).
 * OUTPUT public/work/<slug>/…  (photos, video posters, videos)
 *        src/content/work/projects.generated.json  (what the site renders)
 *
 * Re-running is safe: the manifest is rebuilt from scratch every time and
 * files that already exist on disk are not downloaded again, so nothing is
 * ever duplicated. Delete a project folder to force a fresh download.
 */
import { createWriteStream, existsSync, mkdirSync, readFileSync, statSync, writeFileSync, unlinkSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const WORK_DIR = join(ROOT, "src", "content", "work");
const MEDIA_DIR = join(ROOT, "public", "work");
const OWNER = "thebox.detailing";
const PHOTO_MAX_EDGE = 1600;
const PHOTO_QUALITY = 82;

/* ─────────────────────────────────────────────────────────── arguments */

const args = process.argv.slice(2);
const inputPath = args.find((a) => !a.startsWith("--"));
if (!inputPath) {
  console.error("usage: node scripts/import-instagram.mjs <export.json> [--skip-media] [--videos=selected|all|none] [--max-video-mb=40]");
  process.exit(1);
}
const flag = (name, fallback) => {
  const hit = args.find((a) => a === `--${name}` || a.startsWith(`--${name}=`));
  if (!hit) return fallback;
  return hit.includes("=") ? hit.split("=")[1] : true;
};
const SKIP_MEDIA = flag("skip-media", false) === true;
const VIDEO_MODE = flag("videos", "selected");
const MAX_VIDEO_BYTES = Number(flag("max-video-mb", 40)) * 1024 * 1024;

/* ─────────────────────────────────────────────────────────── helpers */

const readJson = (p) => JSON.parse(readFileSync(p, "utf8"));
const selection = readJson(join(WORK_DIR, "selection.json"));
const glossary = readJson(join(WORK_DIR, "glossary.json"));

/** Must stay identical to the normaliser used to build glossary.json. */
function normalizeLine(line) {
  let s = line.toLowerCase().replace(/ё/g, "е");
  s = s.replace(/#\S+/g, "").replace(/@\S+/g, "");
  s = s.replace(/^[\s•▪️◾️✅✔️—\-–▫️➡️]+/u, "");
  // JavaScript's \b is ASCII-only, so Cyrillic boundaries are spelled out.
  s = s.replace(/(^|[^а-яіїєґ])стёкл/g, "$1стекл");
  s = s.replace(/(^|[^0-9а-яіїєґ])2[- ]?(ух|х)(?![а-яіїєґ])/g, "$1двух");
  s = s.replace(/(^|[^0-9а-яіїєґ])4[- ]?(ех|х)(?![а-яіїєґ])/g, "$1четырех");
  s = s.replace(/[“”"«»]/g, "");
  return s.replace(/\s+/g, " ").replace(/^[\s;.,:]+|[\s;.,:]+$/g, "");
}

const NOISE = /(для запис|telegram|viber|whatsapp|\+380|^the box$|happy halloween|захисне скло від|на даному автомобілі|виконали наступний|захисне скло для автомобільних)/i;
// Only the bare headers — "Выполнили комплекс работ:" — not single-line captions
// such as "Выполнили полную оклейку…", which are real work items.
const HEADER = /^(виконали|выполнили)(\s+комплекс\s+(робіт|работ|услуг|послуг))?:?\s*$/i;
const RULE = /^[➖—\-–\s]+$/;

/** Splits a caption into [vehicleLine, serviceLines[]], dropping the noise. */
function parseCaption(caption) {
  const lines = (caption || "").split("\n");
  const vehicle = (lines[0] || "").replace(/^[\s➡️▶️]+/u, "").trim();
  const services = [];
  for (const raw of lines.slice(1)) {
    const n = normalizeLine(raw);
    if (!n || NOISE.test(n) || HEADER.test(n) || RULE.test(n)) continue;
    services.push(n);
  }
  return { vehicle, services };
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[šś]/g, "s").replace(/[čć]/g, "c").replace(/ž/g, "z")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function canonicalVehicle(raw) {
  const aliases = selection.vehicleAliases || {};
  const key = raw.trim();
  if (aliases[key] !== undefined) return aliases[key];
  const lowerHit = Object.keys(aliases).find((k) => k.toLowerCase() === key.toLowerCase());
  if (lowerHit) return aliases[lowerHit];
  return key;
}

function categoriesFor(serviceKeys, shortCode) {
  const override = selection.categoryOverrides?.[shortCode];
  if (override) return override;
  const found = new Set();
  for (const rule of selection.categories) {
    const patterns = rule.match.map((m) => new RegExp(m, "i"));
    const excludes = (rule.exclude || []).map((m) => new RegExp(m, "i"));
    const hit = serviceKeys.some(
      (line) => patterns.some((p) => p.test(line)) && !excludes.some((e) => e.test(line)),
    );
    if (hit) found.add(rule.id);
  }
  return [...found];
}

/* ─────────────────────────────────────────────────────────── media */

async function fetchToFile(url, dest, { maxBytes } = {}) {
  const res = await fetch(url, { redirect: "follow" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const len = Number(res.headers.get("content-length") || 0);
  if (maxBytes && len > maxBytes) throw new Error(`too large: ${(len / 1048576).toFixed(1)} MB`);
  mkdirSync(dirname(dest), { recursive: true });
  const tmp = `${dest}.part`;
  try {
    await pipeline(Readable.fromWeb(res.body), createWriteStream(tmp));
    if (maxBytes && statSync(tmp).size > maxBytes) throw new Error("too large after download");
    const { renameSync } = await import("node:fs");
    renameSync(tmp, dest);
  } catch (error) {
    if (existsSync(tmp)) unlinkSync(tmp);
    throw error;
  }
}

let sharp = null;
async function loadSharp() {
  if (sharp === null) {
    try {
      sharp = (await import("sharp")).default;
    } catch {
      sharp = false;
      console.warn("sharp is not installed — photos are stored without resizing (npm i -D sharp).");
    }
  }
  return sharp;
}

/** Downloads a photo, resizes it to the site's maximum, returns {width,height} or null on failure. */
async function importPhoto(url, dest, failures, label) {
  if (existsSync(dest)) return await readSize(dest);
  if (SKIP_MEDIA) return null;
  const raw = `${dest}.orig`;
  try {
    await fetchToFile(url, raw);
    const s = await loadSharp();
    if (s) {
      await s(raw).rotate().resize({ width: PHOTO_MAX_EDGE, height: PHOTO_MAX_EDGE, fit: "inside", withoutEnlargement: true })
        .jpeg({ quality: PHOTO_QUALITY, mozjpeg: true }).toFile(dest);
      unlinkSync(raw);
    } else {
      const { renameSync } = await import("node:fs");
      renameSync(raw, dest);
    }
    return await readSize(dest);
  } catch (error) {
    failures.push(`${label}: ${error.message}`);
    if (existsSync(raw)) unlinkSync(raw);
    return null;
  }
}

async function readSize(file) {
  const s = await loadSharp();
  if (!s) return { width: 0, height: 0 };
  const meta = await s(file).metadata();
  return { width: meta.width || 0, height: meta.height || 0 };
}

async function importVideo(url, dest, failures, label) {
  if (existsSync(dest)) return true;
  if (SKIP_MEDIA) return false;
  try {
    await fetchToFile(url, dest, { maxBytes: MAX_VIDEO_BYTES });
    return true;
  } catch (error) {
    failures.push(`${label}: ${error.message}`);
    return false;
  }
}

/* ─────────────────────────────────────────────────────────── main */

const exportData = readJson(resolve(inputPath));
const seen = new Set();
const posts = [];
for (const item of exportData) {
  if (item.ownerUsername !== OWNER) continue;
  if (!item.shortCode || seen.has(item.shortCode)) continue;
  seen.add(item.shortCode);
  posts.push(item);
}
const byCode = new Map(posts.map((p) => [p.shortCode, p]));

const excluded = selection.exclude || {};
const mergedInto = new Map();
for (const [primary, secondaries] of Object.entries(selection.merge || {})) {
  for (const s of secondaries) mergedInto.set(s, primary);
}

const missingGlossary = new Map();
const mediaFailures = [];
const projects = [];
const featuredOrder = new Map((selection.featured || []).map((code, i) => [code, i]));
const videoWanted = new Set(selection.videos || []);

for (const post of posts.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1))) {
  const code = post.shortCode;
  if (excluded[code] || mergedInto.has(code)) continue;

  const { vehicle: rawVehicle, services } = parseCaption(post.caption);
  const vehicle = canonicalVehicle(rawVehicle);
  if (!vehicle) { mediaFailures.push(`${code}: no vehicle line`); continue; }

  const slug = `${slugify(vehicle)}-${code.toLowerCase()}`;
  const sources = [post, ...(selection.merge?.[code] || []).map((c) => byCode.get(c)).filter(Boolean)];
  const dir = join(MEDIA_DIR, slug);

  // Services: translate through the glossary, flagging anything missing.
  const uniq = [...new Set(services)];
  // A glossary entry of { "skip": true } drops the line (credits, greetings,
  // sub-bullets already folded into their parent line).
  const works = uniq
    .map((key) => {
      const entry = glossary[key];
      if (entry?.skip) return null;
      if (!entry || !entry.uk || !entry.en) {
        missingGlossary.set(key, (missingGlossary.get(key) || 0) + 1);
        return { uk: key, en: key, untranslated: true };
      }
      return { uk: entry.uk, en: entry.en };
    })
    .filter((work) => work !== null);

  // Media, in posting order: carousel frames first, then reel posters/videos.
  const photos = [];
  const videos = [];
  let index = 0;
  // Carousels first so the cover is a proper photograph when one exists.
  const ordered = [...sources.filter((s) => s.type === "Sidecar"), ...sources.filter((s) => s.type !== "Sidecar")];
  for (const src of ordered) {
    if (src.type === "Sidecar") {
      const frames = (src.childPosts?.length ? src.childPosts.map((c) => c.displayUrl) : src.images) || [];
      for (const url of frames) {
        index += 1;
        const file = `${String(index).padStart(2, "0")}.jpg`;
        const size = await importPhoto(url, join(dir, file), mediaFailures, `${slug}/${file}`);
        if (size) photos.push({ src: `/work/${slug}/${file}`, ...size, source: src.shortCode });
      }
    } else if (src.type === "Video") {
      const posterFile = `poster-${src.shortCode.toLowerCase()}.jpg`;
      const size = await importPhoto(src.displayUrl, join(dir, posterFile), mediaFailures, `${slug}/${posterFile}`);
      const poster = size ? { src: `/work/${slug}/${posterFile}`, ...size, source: src.shortCode } : null;
      const wantVideo = VIDEO_MODE === "all" || (VIDEO_MODE === "selected" && videoWanted.has(code));
      let videoSrc = null;
      if (wantVideo && src.videoUrl) {
        const videoFile = `video-${src.shortCode.toLowerCase()}.mp4`;
        if (await importVideo(src.videoUrl, join(dir, videoFile), mediaFailures, `${slug}/${videoFile}`)) videoSrc = `/work/${slug}/${videoFile}`;
      }
      if (poster) videos.push({ poster, src: videoSrc, sourceUrl: src.url, source: src.shortCode });
    }
  }

  const cover = photos[0] ?? videos[0]?.poster ?? null;
  projects.push({
    id: code,
    slug,
    vehicle,
    date: post.timestamp,
    sourceUrl: post.url,
    sources: sources.map((s) => s.shortCode),
    categories: categoriesFor(uniq, code),
    works,
    summary: selection.summaries?.[code] ?? null,
    cover,
    photos,
    videos,
    featured: featuredOrder.has(code),
    order: featuredOrder.has(code) ? featuredOrder.get(code) : 1000,
    visible: selection.hidden?.includes(code) ? false : true,
  });
}

// Featured first in their curated order, then newest first.
projects.sort((a, b) => a.order - b.order || (a.date < b.date ? 1 : -1));
projects.forEach((p, i) => { p.order = i; });

const manifest = {
  generatedAt: new Date().toISOString(),
  owner: OWNER,
  stats: {
    postsInExport: exportData.length,
    studioPosts: posts.length,
    excluded: Object.keys(excluded).length,
    mergedAway: mergedInto.size,
    projects: projects.length,
    withCover: projects.filter((p) => p.cover).length,
    photos: projects.reduce((n, p) => n + p.photos.length, 0),
    videosDownloaded: projects.reduce((n, p) => n + p.videos.filter((v) => v.src).length, 0),
    untranslatedLines: missingGlossary.size,
    mediaFailures: mediaFailures.length,
  },
  projects,
};
writeFileSync(join(WORK_DIR, "projects.generated.json"), JSON.stringify(manifest, null, 2) + "\n");
writeFileSync(join(WORK_DIR, "import-report.json"), JSON.stringify({
  generatedAt: manifest.generatedAt,
  stats: manifest.stats,
  untranslated: [...missingGlossary.entries()].sort((a, b) => b[1] - a[1]).map(([key, count]) => ({ key, count })),
  mediaFailures,
}, null, 2) + "\n");

console.log(JSON.stringify(manifest.stats, null, 2));
if (missingGlossary.size) console.log(`\n${missingGlossary.size} service lines have no glossary entry — see src/content/work/import-report.json`);
if (mediaFailures.length) console.log(`${mediaFailures.length} media files could not be downloaded — see import-report.json`);
