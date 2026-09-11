import { NextResponse } from "next/server";
import { site } from "@/content/site";

/**
 * Booking requests → Telegram.
 *
 * The form posts here; the request is forwarded as one message to the chat
 * whose id is in TELEGRAM_CHAT_ID using the bot in TELEGRAM_BOT_TOKEN. Both
 * live in the hosting environment (Vercel → Settings → Environment Variables),
 * never in the repository. Until they are set the endpoint answers
 * `{ ok: false, reason: "not-configured" }` and the form falls back to opening
 * a messenger with the text prefilled, so nothing is lost either way.
 */

export const runtime = "nodejs";

const MAX_LEN = 2000;
const WINDOW_MS = 10 * 60 * 1000;
const MAX_PER_WINDOW = 5;
const recent = new Map<string, number[]>();

type Lead = {
  name: string;
  phone: string;
  email?: string;
  make: string;
  model: string;
  year?: string;
  service?: string;
  date?: string;
  message?: string;
  locale?: string;
  page?: string;
  /** Honeypot: bots fill it, people never see it. */
  company?: string;
};

const clean = (value: unknown, max = 200) =>
  typeof value === "string" ? value.replace(/\s+/g, " ").trim().slice(0, max) : "";

function tooMany(key: string): boolean {
  const now = Date.now();
  const hits = (recent.get(key) ?? []).filter((at) => now - at < WINDOW_MS);
  hits.push(now);
  recent.set(key, hits);
  if (recent.size > 5000) recent.clear();
  return hits.length > MAX_PER_WINDOW;
}

const escape = (value: string) =>
  value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export async function POST(request: Request) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chatId) {
    return NextResponse.json({ ok: false, reason: "not-configured" }, { status: 200 });
  }

  let body: Lead;
  try {
    body = (await request.json()) as Lead;
  } catch {
    return NextResponse.json({ ok: false, reason: "bad-request" }, { status: 400 });
  }

  // Honeypot filled → pretend success so the bot moves on.
  if (clean(body.company)) return NextResponse.json({ ok: true });

  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  if (tooMany(ip)) return NextResponse.json({ ok: false, reason: "rate-limited" }, { status: 429 });

  const name = clean(body.name);
  const phone = clean(body.phone, 40);
  const make = clean(body.make, 60);
  const model = clean(body.model, 60);
  if (name.length < 2 || !/^[+\d][\d\s()-]{7,}$/.test(phone) || make.length < 2 || !model) {
    return NextResponse.json({ ok: false, reason: "invalid" }, { status: 422 });
  }

  const lines = [
    `<b>Нова заявка з сайту</b> — ${escape(site.shortName)}`,
    `👤 ${escape(name)}`,
    `📞 ${escape(phone)}`,
    clean(body.email) ? `✉️ ${escape(clean(body.email))}` : null,
    `🚗 ${escape(make)} ${escape(model)}${clean(body.year, 8) ? ` (${escape(clean(body.year, 8))})` : ""}`,
    clean(body.service, 80) ? `🛠 ${escape(clean(body.service, 80))}` : null,
    clean(body.date, 20) ? `📅 ${escape(clean(body.date, 20))}` : null,
    typeof body.message === "string" && body.message.trim()
      ? `\n${escape(body.message.trim().slice(0, MAX_LEN))}`
      : null,
    `\n<i>${escape(clean(body.locale, 5) || "uk")} · ${escape(clean(body.page, 200) || "/")}</i>`,
  ].filter((line) => line !== null);

  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: lines.join("\n"), parse_mode: "HTML" }),
    signal: AbortSignal.timeout(8000),
  }).catch(() => null);

  if (!response?.ok) {
    return NextResponse.json({ ok: false, reason: "delivery-failed" }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
