import { ResearchScreen } from "@/components/research-screen";
export default async function Page({ params }: { params: Promise<{ strategyId: string }> }) {
  const { strategyId } = await params;
  return <ResearchScreen view="versions" strategyId={strategyId} />;
}
