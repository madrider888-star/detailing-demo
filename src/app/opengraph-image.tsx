import { ImageResponse } from "next/og";
import { site } from "@/content/site";

export const alt = `${site.name} — ${site.tagline}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Social card. Rendered at build time so it works without a network call. */
export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 72,
          backgroundColor: "#050607",
          backgroundImage:
            "radial-gradient(900px 520px at 22% 8%, #1b2229 0%, rgba(5,6,7,0) 62%), radial-gradient(760px 460px at 92% 96%, #14181d 0%, rgba(5,6,7,0) 60%)",
          color: "#e8ebee",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <svg width="46" height="46" viewBox="0 0 32 32">
            <path d="M16 3.5 29 28.5H22.6L16 15.2 9.4 28.5H3L16 3.5Z" fill="#e8ebee" />
          </svg>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: 22, letterSpacing: 6, fontWeight: 600 }}>APEX</span>
            <span style={{ fontSize: 13, letterSpacing: 8, color: "#79828b", marginTop: 4 }}>
              DETAILING
            </span>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ fontSize: 16, letterSpacing: 5, color: "#d9b778" }}>
            ODESSA · EST. 2014
          </span>
          <span
            style={{
              fontSize: 66,
              lineHeight: 1.06,
              fontWeight: 700,
              letterSpacing: -1.6,
              marginTop: 26,
              maxWidth: 900,
            }}
          >
            Protection that keeps the paint you paid for.
          </span>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: "1px solid rgba(232,235,238,0.12)",
            paddingTop: 28,
            fontSize: 21,
            color: "#9aa2ab",
          }}
        >
          <span>Ceramic Coating · PPF · Paint Correction</span>
          <span style={{ color: "#e8ebee" }}>apexdetailing.demo</span>
        </div>
      </div>
    ),
    size,
  );
}
