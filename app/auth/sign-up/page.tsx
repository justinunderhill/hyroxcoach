import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

export default async function SignUpPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <section className="w-full max-w-md rounded-[2rem] border border-line bg-surface p-7 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-10">
        <Link className="text-sm font-bold text-lime" href="/">
          ← HYROX Coach
        </Link>
        <h1 className="mt-8 text-3xl font-semibold tracking-[-0.045em] text-ink">Create your account</h1>
        <p className="mt-2 text-sm leading-6 text-muted">Your records remain yours, even when you train as a team.</p>
        <AuthForm mode="sign-up" next={next} />
      </section>
    </main>
  );
}
