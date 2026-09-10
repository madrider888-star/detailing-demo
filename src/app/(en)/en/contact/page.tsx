import { ContactView } from "@/views/contact-view";
import { contactMeta } from "@/views/meta";
import { getService } from "@/content/services";

export const metadata = contactMeta("en");

/** `?service=<slug>` preselects a service in the booking form. */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ service?: string }>;
}) {
  const { service } = await searchParams;
  const preselected = service && getService(service) ? service : "";

  return <ContactView locale="en" defaultService={preselected} />;
}
