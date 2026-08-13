import Link from "next/link";
import { redirect } from "next/navigation";

import { CindyClient } from "@/components/cindy-client";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function CindyPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-6 sm:px-8 sm:py-10">
      <div className="mx-auto max-w-2xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">Benchmark</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-[-0.045em] text-ink">Cindy</h1>
          </div>
          <Link className="text-xs font-semibold text-muted" href="/dashboard">
            Close
          </Link>
        </div>
        <p className="mt-1 text-sm leading-6 text-muted">Not a HYROX simulation — a strength and conditioning benchmark.</p>

        <section className="mt-6">
          <CindyClient />
        </section>
      </div>
    </main>
  );
}
