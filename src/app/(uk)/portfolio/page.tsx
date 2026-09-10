import { PortfolioView } from "@/views/portfolio-view";
import { portfolioMeta } from "@/views/meta";

export const metadata = portfolioMeta("uk");

export default function Page() {
  return <PortfolioView locale="uk" />;
}
