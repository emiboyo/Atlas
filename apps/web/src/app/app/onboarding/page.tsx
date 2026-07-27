import { OnboardingPanel } from "@/components/onboarding-panel";

export default function OnboardingPage() {
  return (
    <>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">Onboarding</p>
      <h1 className="font-display mt-3 text-4xl font-semibold">Set up your Atlas identity</h1>
      <OnboardingPanel />
    </>
  );
}
