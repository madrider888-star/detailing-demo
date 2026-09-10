import { ContactView } from "@/views/contact-view";
import { contactMeta } from "@/views/meta";
import { getService } from "@/content/services";
import { getWorkProject } from "@/content/work";
import { ui } from "@/content/ui";
import { t } from "@/lib/i18n";

const locale = "en" as const;

export const metadata = contactMeta(locale);

/**
 * `?service=<slug>` preselects a service; `?project=<slug>` prefills the
 * message with "I'd like a similar project" for that piece of work.
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ service?: string; project?: string }>;
}) {
  const { service, project } = await searchParams;
  const preselected = service && getService(service) ? service : "";

  const work = project ? getWorkProject(project) : undefined;
  const message = work
    ? t(ui.work.similarPrefill, locale)
        .replace("{vehicle}", work.vehicle)
        .replace("{works}", work.works.map((item) => item[locale]).join("; "))
    : "";

  return <ContactView locale={locale} defaultService={preselected} defaultMessage={message} />;
}
