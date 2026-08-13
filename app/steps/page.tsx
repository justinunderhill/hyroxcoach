import { redirect } from "next/navigation";

import { StepsClient } from "@/components/steps-client";
import { PageHeader } from "@/components/page-header";
import { getServerAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function StepsPage() {
  const { data: session } = await getServerAuth().getSession();
  if (!session?.user) redirect("/auth/sign-in");

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-2xl">
        <PageHeader eyebrow="Steps" title="Daily steps" />
        <p className="mt-2 text-sm leading-6 text-muted">Context for activity level — not a HYROX readiness score by itself.</p>

        <section className="mt-8">
          <StepsClient />
        </section>
      </div>
    </main>
  );
}
