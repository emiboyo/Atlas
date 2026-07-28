import { PortfolioWorkspace } from "@/components/portfolio-workspace";

export default async function PortfolioHoldingsPage({
  params,
}: {
  params: Promise<{ portfolioId: string }>;
}) {
  const { portfolioId } = await params;
  return <PortfolioWorkspace portfolioId={portfolioId} view="holdings" />;
}
