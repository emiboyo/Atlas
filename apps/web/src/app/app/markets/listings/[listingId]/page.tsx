import { MarketListing } from "@/components/market-listing";

export default async function ListingPage({ params }: { params: Promise<{ listingId: string }> }) {
  const { listingId } = await params;
  return <MarketListing listingId={listingId} />;
}
