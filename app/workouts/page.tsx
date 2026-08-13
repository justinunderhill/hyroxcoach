import { redirect } from "next/navigation";

import { getServerAuth } from "@/lib/auth/server";
import { WorkoutsClient } from "@/components/workouts-client";

export const dynamic = "force-dynamic";

export default async function WorkoutsPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-3xl">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">Training log</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-[-0.045em] text-ink">Log a workout</h1>
        <p className="mt-2 text-sm leading-6 text-muted">Runs, MMA, strength, walks or HYROX-specific work — tag categories that apply.</p>

        <section className="mt-8 rounded-[2rem] border border-line bg-surface p-6 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-8">
          <WorkoutsClient />
        </section>
      </div>
    </main>
  );
}
