import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import sharp from "sharp";
import { site } from "@/content/site";
import { ui } from "@/content/ui";
import { t, type Locale } from "@/lib/i18n";
import type { WorkProject } from "@/types";

/**
 * Social cards (Open Graph / Twitter). Rendered at build time from the
 * project's own cover photo, so a link pasted into Telegram, Instagram or
 * WhatsApp previews as a magazine cover: the car, its name and the studio.
 */

export const OG_SIZE = { width: 1200, height: 630 };
export const OG_CONTENT_TYPE = "image/jpeg";

const FONT_PATH = join(process.cwd(), "src", "assets", "fonts", "Manrope-Bold.ttf");

let fontCache: Promise<ArrayBuffer> | null = null;
function font(): Promise<ArrayBuffer> {
  fontCache ??= readFile(FONT_PATH).then((buffer) =>
    buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength),
  );
  return fontCache;
}

/** A public/ photo, cropped to the card's frame and inlined — the renderer has no network. */
async function photoDataUrl(src: string, width: number, height: number): Promise<string | null> {
  try {
    const file = await readFile(join(process.cwd(), "public", src));
    const jpeg = await sharp(file)
      .resize({ width, height, fit: "cover", position: "attention" })
      .jpeg({ quality: 78, mozjpeg: true })
      .toBuffer();
    return `data:image/jpeg;base64,${jpeg.toString("base64")}`;
  } catch {
    return null;
  }
}

async function logoDataUrl(): Promise<string | null> {
  try {
    const file = await readFile(join(process.cwd(), "public", "images", "brand", "logo-mark.png"));
    return `data:image/png;base64,${file.toString("base64")}`;
  } catch {
    return null;
  }
}

function Card({
  photo,
  logo,
  eyebrow,
  title,
  lines,
  footer,
}: {
  photo: string | null;
  logo: string | null;
  eyebrow: string;
  title: string;
  lines: string[];
  footer: string;
}) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        position: "relative",
        backgroundColor: "#050505",
        color: "#ffffff",
        fontFamily: "Manrope",
      }}
    >
      {photo ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={photo}
          alt=""
          width={OG_SIZE.width}
          height={OG_SIZE.height}
          style={{ position: "absolute", top: 0, left: 0, width: OG_SIZE.width, height: OG_SIZE.height, objectFit: "cover" }}
        />
      ) : null}
      {/* Satori needs explicit boxes: `inset` alone collapses to nothing. */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: OG_SIZE.width,
          height: OG_SIZE.height,
          backgroundImage:
            "linear-gradient(90deg, rgba(5,5,5,0.94) 0%, rgba(5,5,5,0.6) 50%, rgba(5,5,5,0.12) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: OG_SIZE.width,
          height: OG_SIZE.height,
          backgroundImage: "linear-gradient(0deg, rgba(5,5,5,0.92) 0%, rgba(5,5,5,0) 50%)",
        }}
      />

      <div
        style={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          width: "100%",
          height: "100%",
          padding: "56px 64px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
          {logo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logo} alt="" width={92} height={65} />
          ) : null}
          <span style={{ fontSize: 20, letterSpacing: 6, textTransform: "uppercase", color: "#c8cacd" }}>
            {eyebrow}
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", maxWidth: 820 }}>
          <span
            style={{
              fontSize: title.length > 22 ? 64 : 84,
              lineHeight: 1.02,
              fontWeight: 700,
              letterSpacing: -2,
              textTransform: "uppercase",
            }}
          >
            {title}
          </span>
          {lines.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", marginTop: 26, gap: 8 }}>
              {lines.map((line) => (
                <span key={line} style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 24, color: "#c8cacd" }}>
                  <span style={{ width: 18, height: 2, backgroundColor: "#ffffff", opacity: 0.6 }} />
                  {line}
                </span>
              ))}
            </div>
          ) : null}
          <span style={{ marginTop: 34, fontSize: 20, letterSpacing: 4, textTransform: "uppercase", color: "#9b9ea4" }}>
            {footer}
          </span>
        </div>
      </div>
    </div>
  );
}

/** Renders the card and re-encodes it as JPEG: a photographic PNG would be ~1 MB, the JPEG ~120 kB. */
async function render(props: Parameters<typeof Card>[0]) {
  const png = await new ImageResponse(<Card {...props} />, {
    ...OG_SIZE,
    fonts: [{ name: "Manrope", data: await font(), weight: 700, style: "normal" }],
  }).arrayBuffer();
  const jpeg = await sharp(Buffer.from(png)).jpeg({ quality: 84, mozjpeg: true }).toBuffer();
  return new Response(new Uint8Array(jpeg), {
    headers: { "content-type": "image/jpeg", "cache-control": "public, max-age=31536000, immutable" },
  });
}

/** Card for one project in "Our work". */
export async function projectOgImage(project: WorkProject, locale: Locale) {
  const [photo, logo] = await Promise.all([
    project.cover ? photoDataUrl(project.cover.src, OG_SIZE.width, OG_SIZE.height) : null,
    logoDataUrl(),
  ]);
  return render({
    photo,
    logo,
    eyebrow: t(ui.nav.portfolio, locale),
    title: project.vehicle,
    lines: project.works.slice(0, 3).map((item) => truncate(item[locale], 54)),
    footer: `${site.name} · ${site.instagram.handle}`,
  });
}

/** Card for the home page and every page without its own photograph. */
export async function siteOgImage(locale: Locale) {
  const poster = site.hero.video?.poster.src ?? site.hero.media?.src ?? null;
  const [photo, logo] = await Promise.all([
    poster ? photoDataUrl(poster, OG_SIZE.width, OG_SIZE.height) : null,
    logoDataUrl(),
  ]);
  return render({
    photo,
    logo,
    eyebrow: t(site.tagline, locale),
    title: site.name,
    lines: [t(site.hero.subline, locale)],
    footer: site.instagram.handle,
  });
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1).trimEnd()}…` : text;
}
