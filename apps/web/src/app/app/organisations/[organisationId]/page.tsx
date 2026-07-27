export default async function OrganisationSettingsPage({
  params,
}: {
  params: Promise<{ organisationId: string }>;
}) {
  const { organisationId } = await params;
  return (
    <>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">
        Workspace settings
      </p>
      <h1 className="font-display mt-3 text-4xl font-semibold">Organisation and members</h1>
      <p className="mt-4 max-w-2xl text-slate-300">
        Membership controls are enforced by the API permission matrix. Unauthorised controls are
        denied server-side even if a workspace identifier is modified.
      </p>
      <OrganisationPanel organisationId={organisationId} />
    </>
  );
}
import { OrganisationPanel } from "@/components/organisation-panel";
