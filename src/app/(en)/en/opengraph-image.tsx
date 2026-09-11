import { OG_CONTENT_TYPE, OG_SIZE, siteOgImage } from "@/lib/og";

const locale = "en" as const;

export const alt = "THE BOX Detailing";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  return siteOgImage(locale);
}
