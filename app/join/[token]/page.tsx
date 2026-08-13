import Link from "next/link";
import { redirect } from "next/navigation";

import { JoinTeamAction } from "@/components/join-team-action";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function JoinTeamPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const { data: session } = await getServerAuth().getSession();

  if (!session?.user) {
    redirect(`/auth/sign-in?next=/join/${token}`);
  }

  return (
    <main className="min-h-screen px-5 py-8 sm:py-12">
      <section className="mx-auto max-w-lg rounded-[2rem] border border-line bg-surface p-7 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-10">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">
          Team invite
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-ink">
          Join your partner&apos;s team
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-muted">
          Accepting this invite links your account to their HYROX Doubles team. If you already
          belong to another team, you&apos;ll leave it for this one.
        </p>
        <JoinTeamAction token={token} />
        <Link className="mt-6 inline-block text-xs font-semibold text-muted" href="/dashboard">
          Cancel and go to dashboard
        </Link>
      </section>
    </main>
  );
}
