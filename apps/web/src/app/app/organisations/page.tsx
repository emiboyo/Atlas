import { OrganisationList } from "@/components/organisation-list";

export default function OrganisationsPage() {
  return (
    <>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">Workspaces</p>
      <h1 className="font-display mt-3 text-4xl font-semibold">Organisation access</h1>
      <p className="mt-4 max-w-2xl text-slate-300">
        Switch between your personal workspace and team organisations.
      </p>
      <OrganisationList />
    </>
  );
}
