import Link from "next/link";
import { redirect } from "next/navigation";

import { ProfileSummary } from "@/components/profile-summary";
import { SignOutButton } from "@/components/sign-out-button";
import { WeeklyStats } from "@/components/weekly-stats";
import { WorkoutFeed } from "@/components/workout-feed";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-5xl">
        <header className="flex items-center justify-between gap-5">
          <div>
            <p className="text-sm text-stone-500">Signed in as {session.user.email}</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-[-0.045em] text-[#15221b]">Your dashboard</h1>
          </div>
          <SignOutButton />
        </header>
        <section className="mt-8 grid gap-5 md:grid-cols-3">
          <ProfileSummary />
          <div className="rounded-3xl border border-[#dbe998] bg-[#f8ffe4] p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Log</p>
            <h2 className="mt-2 text-xl font-semibold text-[#263711]">Log a workout</h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">Runs, MMA, strength, walks or HYROX-specific work.</p>
            <Link className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-[#15271e] px-4 text-sm font-bold text-white" href="/workouts">Log workout</Link>
          </div>
          <div className="rounded-3xl border border-stone-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Log</p>
            <h2 className="mt-2 text-xl font-semibold text-[#15221b]">Meals & measurements</h2>
            <p className="mt-2 text-sm leading-6 text-stone-500">Track nutrition and bodyweight/waist trends.</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link className="inline-flex min-h-11 items-center rounded-xl border border-stone-300 px-4 text-sm font-semibold text-stone-700" href="/meals">Log meal</Link>
              <Link className="inline-flex min-h-11 items-center rounded-xl border border-stone-300 px-4 text-sm font-semibold text-stone-700" href="/measurements">Log measurement</Link>
              <Link className="inline-flex min-h-11 items-center rounded-xl border border-stone-300 px-4 text-sm font-semibold text-stone-700" href="/nutrition">Nutrition targets</Link>
            </div>
          </div>
        </section>
        <section className="mt-8">
          <WeeklyStats />
        </section>
        <section className="mt-8">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Recent activity</p>
          <div className="mt-3">
            <WorkoutFeed />
          </div>
        </section>
      </div>
    </main>
  );
}
