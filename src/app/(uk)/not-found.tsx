import { NotFoundView } from "@/views/not-found-view";

export const metadata = { title: "404", robots: { index: false, follow: true } };

export default function NotFound() {
  return <NotFoundView locale="uk" />;
}
