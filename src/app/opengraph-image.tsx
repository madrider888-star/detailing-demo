import { ImageResponse } from "next/og";
import { site } from "@/content/site";

export const alt = site.name;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/**
 * Social card. Deliberately typographic — it is replaced with a photographic
 * card once THE BOX supplies imagery.
 */
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
          padding: 80,
          backgroundColor: "#050505",
          color: "#ffffff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <svg width="44" height="44" viewBox="0 0 32 32">
            <rect x="4" y="4" width="24" height="24" fill="none" stroke="#ffffff" strokeWidth="2.5" />
            <rect x="12" y="12" width="8" height="8" fill="#ffffff" />
          </svg>
          <span style={{ fontSize: 22, letterSpacing: 8, fontWeight: 700 }}>THE BOX</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <span
            style={{
              fontSize: 96,
              lineHeight: 1,
              fontWeight: 800,
              letterSpacing: -3,
              textTransform: "uppercase",
            }}
          >
            Detailing
          </span>
          <span style={{ fontSize: 28, color: "#9b9ea4", marginTop: 28 }}>
            {site.instagram.handle}
          </span>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            borderTop: "1px solid rgba(255,255,255,0.15)",
            paddingTop: 30,
            fontSize: 20,
            color: "#9b9ea4",
          }}
        >
          <span>{site.name}</span>
        </div>
      </div>
    ),
    size,
  );
}
