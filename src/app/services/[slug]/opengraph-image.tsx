import { ImageResponse } from "next/og";
import { getService, services, categoryLabels } from "@/content/services";
import { site } from "@/content/site";
import { formatPrice } from "@/lib/utils";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Apex Detailing service";

export function generateStaticParams() {
  return services.map((service) => ({ slug: service.slug }));
}

/** Per-service social card, rendered to PNG at build time. */
export default async function ServiceOpenGraphImage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const service = getService(slug);
  const title = service?.title ?? site.name;

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
            "radial-gradient(880px 500px at 80% 10%, #1b2229 0%, rgba(5,6,7,0) 62%), radial-gradient(700px 420px at 8% 92%, #14181d 0%, rgba(5,6,7,0) 58%)",
          color: "#e8ebee",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <svg width="40" height="40" viewBox="0 0 32 32">
            <path d="M16 3.5 29 28.5H22.6L16 15.2 9.4 28.5H3L16 3.5Z" fill="#e8ebee" />
          </svg>
          <span style={{ fontSize: 20, letterSpacing: 6, fontWeight: 600 }}>APEX DETAILING</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ fontSize: 16, letterSpacing: 5, color: "#d9b778" }}>
            {(service ? categoryLabels[service.category] : "Studio").toUpperCase()}
          </span>
          <span
            style={{
              fontSize: 78,
              lineHeight: 1.04,
              fontWeight: 700,
              letterSpacing: -2,
              marginTop: 22,
              maxWidth: 940,
            }}
          >
            {title}
          </span>
          {service ? (
            <span style={{ fontSize: 26, color: "#9aa2ab", marginTop: 24, maxWidth: 880 }}>
              {service.tagline}
            </span>
          ) : null}
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: "1px solid rgba(232,235,238,0.12)",
            paddingTop: 28,
            fontSize: 22,
            color: "#9aa2ab",
          }}
        >
          <span>
            {service ? `From ${formatPrice(service.priceFrom)} · ${service.duration}` : site.tagline}
          </span>
          <span style={{ color: "#e8ebee" }}>apexdetailing.demo</span>
        </div>
      </div>
    ),
    size,
  );
}
