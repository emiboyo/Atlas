import { MarketInstrument } from "@/components/market-instrument";

export default async function InstrumentPage({
  params,
}: {
  params: Promise<{ instrumentId: string }>;
}) {
  const { instrumentId } = await params;
  return <MarketInstrument instrumentId={instrumentId} />;
}
