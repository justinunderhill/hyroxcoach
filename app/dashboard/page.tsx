import { redirect } from "next/navigation";

import { ProfileSummary } from "@/components/profile-summary";
import { SignOutButton } from "@/components/sign-out-button";
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
        <section className="mt-8 grid gap-5 md:grid-cols-2">
          <ProfileSummary />
          <div className="rounded-3xl border border-dashed border-stone-300 bg-white/50 p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Next</p>
            <h2 className="mt-2 text-xl font-semibold text-[#15221b]">Create or join your team</h2>
            <p className="mt-2 text-sm leading-6 text-stone-500">Team invitations and the target HYROX event arrive in the next product vertical.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
