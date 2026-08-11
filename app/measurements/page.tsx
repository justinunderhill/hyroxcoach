import { redirect } from "next/navigation";

import { MeasurementsClient } from "@/components/measurements-client";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function MeasurementsPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-3xl">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#567118]">Measurements</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-[-0.045em] text-[#15221b]">Log a measurement</h1>
        <p className="mt-2 text-sm leading-6 text-stone-500">Private by default — share with your team only if you choose to.</p>

        <section className="mt-8 rounded-[2rem] border border-white/70 bg-white p-6 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-8">
          <MeasurementsClient />
        </section>
      </div>
    </main>
  );
}
