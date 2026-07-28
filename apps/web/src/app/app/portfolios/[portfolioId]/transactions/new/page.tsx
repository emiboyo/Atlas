import { PortfolioTransactionForm } from "@/components/portfolio-transaction-form";

export default async function NewPortfolioTransactionPage({
  params,
}: {
  params: Promise<{ portfolioId: string }>;
}) {
  const { portfolioId } = await params;
  return <PortfolioTransactionForm portfolioId={portfolioId} />;
}
