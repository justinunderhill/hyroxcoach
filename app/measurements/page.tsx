import { redirect } from "next/navigation";

import { MeasurementsClient } from "@/components/measurements-client";
import { PageHeader } from "@/components/page-header";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function MeasurementsPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-3xl">
        <PageHeader eyebrow="Measurements" title="Log a measurement" />
        <p className="mt-2 text-sm leading-6 text-muted">Private by default — share with your team only if you choose to.</p>

        <section className="mt-8 rounded-[2rem] border border-line bg-surface p-6 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-8">
          <MeasurementsClient />
        </section>
      </div>
    </main>
  );
}
