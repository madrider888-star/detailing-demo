import type { ReactNode } from "react";
import { SiteShell } from "@/views/site-shell";
import { rootMetadata, viewport } from "@/views/meta";
import "@/app/globals.css";

export const metadata = rootMetadata("uk");
export { viewport };

export default function RootLayout({ children }: { children: ReactNode }) {
  return <SiteShell locale="uk">{children}</SiteShell>;
}
