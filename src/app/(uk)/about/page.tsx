import { AboutView } from "@/views/about-view";
import { aboutMeta } from "@/views/meta";

export const metadata = aboutMeta("uk");

export default function Page() {
  return <AboutView locale="uk" />;
}
