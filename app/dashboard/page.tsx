import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";

import { BottomNav } from "@/components/bottom-nav";
import { ExerciseProgress } from "@/components/exercise-progress";
import { GoalEventCard } from "@/components/goal-event-card";
import { InstallPrompt } from "@/components/install-prompt";
import { ProfileSummary } from "@/components/profile-summary";
import { SignOutButton } from "@/components/sign-out-button";
import { TeamComparison } from "@/components/team-comparison";
import { TeamInviteCard } from "@/components/team-invite-card";
import { TeamWeeklyReview } from "@/components/team-weekly-review";
import { WeeklyReview } from "@/components/weekly-review";
import { WeeklyStats } from "@/components/weekly-stats";
import { WorkoutFeed } from "@/components/workout-feed";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 pb-28 pt-6 sm:px-8 sm:pt-10">
      <div className="mx-auto max-w-5xl">
        <header className="flex items-center justify-between gap-5">
          <Image alt="HYROX Coach" height={36} priority src="/logo.png" width={141} className="h-9 w-auto" />
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-muted sm:inline">{session.user.email}</span>
            <SignOutButton />
          </div>
        </header>

        <section className="mt-6">
          <GoalEventCard />
        </section>

        <section className="mt-5">
          <WeeklyStats />
        </section>

        <section className="mt-5 grid gap-4 sm:grid-cols-2">
          <ProfileSummary />
          <div className="rounded-3xl border border-line bg-surface p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Log</p>
            <h2 className="mt-2 text-lg font-semibold text-ink">Meals &amp; measurements</h2>
            <p className="mt-2 text-sm leading-6 text-muted">Track nutrition and bodyweight/waist trends.</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link className="inline-flex min-h-10 items-center rounded-xl border border-line-strong px-3 text-xs font-semibold text-ink" href="/meals">Log meal</Link>
              <Link className="inline-flex min-h-10 items-center rounded-xl border border-line-strong px-3 text-xs font-semibold text-ink" href="/measurements">Log measurement</Link>
              <Link className="inline-flex min-h-10 items-center rounded-xl border border-line-strong px-3 text-xs font-semibold text-ink" href="/nutrition">Nutrition targets</Link>
              <Link className="inline-flex min-h-10 items-center rounded-xl border border-line-strong px-3 text-xs font-semibold text-ink" href="/steps">Log steps</Link>
            </div>
          </div>
        </section>

        <section className="mt-5 scroll-mt-6" id="progress">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-faint">Progress</p>
          <ExerciseProgress />
        </section>

        <section className="mt-5 scroll-mt-6" id="team">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-faint">Team</p>
          <div className="grid gap-4">
            <TeamComparison />
            <TeamInviteCard />
          </div>
        </section>

        <section className="mt-5 scroll-mt-6" id="coach">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-faint">Coach</p>
          <div className="grid gap-4 sm:grid-cols-2">
            <WeeklyReview />
            <TeamWeeklyReview />
          </div>
        </section>

        <section className="mt-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-faint">Recent activity</p>
          <WorkoutFeed />
        </section>
      </div>

      <BottomNav />
      <InstallPrompt />
    </main>
  );
}
