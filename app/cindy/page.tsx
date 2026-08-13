import { redirect } from "next/navigation";

import { CindyClient } from "@/components/cindy-client";
import { PageHeader } from "@/components/page-header";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function CindyPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-6 sm:px-8 sm:py-10">
      <div className="mx-auto max-w-2xl">
        <PageHeader eyebrow="Benchmark" title="Cindy" size="md" />
        <p className="mt-1 text-sm leading-6 text-muted">Not a HYROX simulation — a strength and conditioning benchmark.</p>

        <section className="mt-6">
          <CindyClient />
        </section>
      </div>
    </main>
  );
}
