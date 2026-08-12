import { redirect } from "next/navigation";

import { NutritionClient } from "@/components/nutrition-client";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function NutritionPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-2xl">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#567118]">Nutrition</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-[-0.045em] text-[#15221b]">Daily targets</h1>
        <p className="mt-2 text-sm leading-6 text-stone-500">Set optional calorie/macro targets and track today against them.</p>

        <section className="mt-8">
          <NutritionClient />
        </section>
      </div>
    </main>
  );
}
