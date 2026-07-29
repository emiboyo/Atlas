import { ResearchScreen } from "@/components/research-screen";
export default async function Page({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  return <ResearchScreen view="events" runId={runId} />;
}
