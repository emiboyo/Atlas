import { WatchlistDetail } from "@/components/watchlist-detail";

export default async function WatchlistPage({
  params,
}: {
  params: Promise<{ watchlistId: string }>;
}) {
  const { watchlistId } = await params;
  return <WatchlistDetail watchlistId={watchlistId} />;
}
