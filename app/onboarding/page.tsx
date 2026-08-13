import { redirect } from "next/navigation";

import { OnboardingForm } from "@/components/onboarding-form";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) {
    redirect("/auth/sign-in");
  }

  return (
    <main className="min-h-screen px-5 py-8 sm:py-12">
      <section className="mx-auto max-w-2xl rounded-[2rem] border border-line bg-surface p-7 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-10">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">Athlete profile</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-ink sm:text-4xl">Set up your training context</h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-muted">Only your name and timezone are required. Baselines help measure progress but can be added later.</p>
        <OnboardingForm initialName={session.user.name ?? ""} />
      </section>
    </main>
  );
}
