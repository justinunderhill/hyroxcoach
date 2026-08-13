import { redirect } from "next/navigation";

import { NutritionClient } from "@/components/nutrition-client";
import { PageHeader } from "@/components/page-header";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function NutritionPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-2xl">
        <PageHeader eyebrow="Nutrition" title="Daily targets" />
        <p className="mt-2 text-sm leading-6 text-muted">Set optional calorie/macro targets and track today against them.</p>

        <section className="mt-8">
          <NutritionClient />
        </section>
      </div>
    </main>
  );
}
