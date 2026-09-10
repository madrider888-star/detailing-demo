import { AboutView } from "@/views/about-view";
import { aboutMeta } from "@/views/meta";

export const metadata = aboutMeta("en");

export default function Page() {
  return <AboutView locale="en" />;
}
