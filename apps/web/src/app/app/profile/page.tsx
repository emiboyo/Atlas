import { ProfileForm } from "@/components/profile-form";
import { DeactivationPanel } from "@/components/deactivation-panel";

export default function ProfilePage() {
  return (
    <>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">Profile</p>
      <h1 className="font-display mt-3 text-4xl font-semibold">Personal settings</h1>
      <p className="mt-4 max-w-2xl text-slate-300">
        Atlas stores only the application information required for this foundation.
      </p>
      <ProfileForm />
      <DeactivationPanel />
    </>
  );
}
