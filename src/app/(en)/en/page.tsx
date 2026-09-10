import { HomeView } from "@/views/home-view";
import { homeMeta } from "@/views/meta";

export const metadata = homeMeta("en");

export default function Page() {
  return <HomeView locale="en" />;
}
