import { ServicesView } from "@/views/services-view";
import { servicesMeta } from "@/views/meta";

export const metadata = servicesMeta("uk");

export default function Page() {
  return <ServicesView locale="uk" />;
}
