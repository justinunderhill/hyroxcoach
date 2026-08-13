import { redirect } from "next/navigation";

import { MealsClient } from "@/components/meals-client";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function MealsPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-3xl">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">Nutrition</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-[-0.045em] text-ink">Log a meal</h1>
        <p className="mt-2 text-sm leading-6 text-muted">Calories and macros are optional — log what you know.</p>

        <section className="mt-8 rounded-[2rem] border border-line bg-surface p-6 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-8">
          <MealsClient />
        </section>
      </div>
    </main>
  );
}
